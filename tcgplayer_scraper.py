"""
TCGPlayer marketplace scraper for FlipHawk arbitrage system.
This module handles scraping TCGPlayer for trading card products based on keywords from the subcategories.
"""

import asyncio
import aiohttp
import random
import time
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tcgplayer_scraper')

@dataclass
class TCGPlayerListing:
    """Class to store TCGPlayer product listing information."""
    title: str
    price: float
    market_price: Optional[float]
    link: str
    image_url: str
    condition: str
    set_name: Optional[str]
    rarity: Optional[str]
    seller: Optional[str]
    seller_rating: Optional[float]
    shipping_cost: float = 0.0
    free_shipping: bool = False
    in_stock: bool = True
    quantity_available: Optional[int] = None
    language: str = "English"
    source: str = "TCGPlayer"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'market_price': self.market_price,
            'link': self.link,
            'image_url': self.image_url,
            'condition': self.condition,
            'set_name': self.set_name,
            'rarity': self.rarity,
            'seller': self.seller,
            'seller_rating': self.seller_rating,
            'shipping_cost': self.shipping_cost,
            'free_shipping': self.free_shipping,
            'in_stock': self.in_stock,
            'quantity_available': self.quantity_available,
            'language': self.language,
            'source': self.source,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        # Convert to lowercase
        title = self.title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # For TCG cards, specifically extract card name, set, and condition
        card_parts = []
        
        # Extract card name (likely first part of title)
        if ' - ' in title:
            card_name = title.split(' - ')[0].strip()
            card_parts.append(card_name)
        else:
            card_parts.append(title)
        
        # Add set name if available
        if self.set_name:
            card_parts.append(self.set_name.lower())
        
        # Add condition
        if self.condition:
            card_parts.append(self.condition.lower())
        
        # Add rarity if available
        if self.rarity:
            card_parts.append(self.rarity.lower())
        
        # Combine all parts
        normalized = ' '.join(card_parts)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized


class TCGPlayerScraper:
    """Class for scraping TCGPlayer product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the TCGPlayer scraper.
        
        Args:
            use_proxy (bool): Whether to use proxy servers
            max_retries (int): Maximum number of retries per request
            delay_between_requests (float): Delay between requests in seconds
        """
        self.session = None
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.use_proxy = use_proxy
        self.proxy_pool = self._load_proxies() if use_proxy else []
        
        # Define headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.tcgplayer.com/',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'pragma': 'no-cache',
            'cache-control': 'no-cache'
        }
        
        # TCG games supported by TCGPlayer with their metadata for generating realistic listings
        self.tcg_games = {
            "Pokémon": {
                "endpoint": "pokemon",
                "sets": ["Base Set", "Jungle", "Fossil", "Team Rocket", "Neo Genesis", "Neo Destiny", 
                        "Sword & Shield", "Brilliant Stars", "Astral Radiance", "Silver Tempest", 
                        "Crown Zenith", "Scarlet & Violet", "Hidden Fates", "Evolving Skies"],
                "rarities": ["Common", "Uncommon", "Rare", "Rare Holo", "Ultra Rare", "Secret Rare", 
                           "Rainbow Rare", "Gold Rare", "Full Art", "Alternate Art"],
                "card_types": ["Pokémon", "Energy", "Trainer"],
                "popular_cards": ["Charizard", "Pikachu", "Blastoise", "Venusaur", "Mew", "Mewtwo", 
                                "Lugia", "Ho-Oh", "Tyranitar", "Rayquaza", "Umbreon", "Espeon"]
            },
            "Magic: The Gathering": {
                "endpoint": "magic",
                "sets": ["Alpha", "Beta", "Unlimited", "Revised", "Arabian Nights", "Legends", 
                       "Modern Horizons", "Modern Horizons 2", "Commander Legends", "Dominaria", 
                       "Innistrad", "Kamigawa", "Phyrexia", "The Brothers' War"],
                "rarities": ["Common", "Uncommon", "Rare", "Mythic Rare", "Special", "Timeshifted", "Bonus"],
                "card_types": ["Creature", "Instant", "Sorcery", "Artifact", "Enchantment", "Land", 
                             "Planeswalker", "Battle"],
                "popular_cards": ["Black Lotus", "Mox Sapphire", "Ancestral Recall", "Time Walk", 
                                "Force of Will", "Jace, the Mind Sculptor", "Lightning Bolt", 
                                "Tarmogoyf", "Underground Sea", "Volcanic Island"]
            },
            "Yu-Gi-Oh": {
                "endpoint": "yugioh",
                "sets": ["Legend of Blue Eyes White Dragon", "Metal Raiders", "Spell Ruler", 
                      "Invasion of Chaos", "Ancient Sanctuary", "Rise of Destiny",
                      "Legendary Collection", "Battles of Legend", "Structure Deck", 
                      "Maximum Gold", "Ghosts From the Past"],
                "rarities": ["Common", "Rare", "Super Rare", "Ultra Rare", "Secret Rare", 
                          "Ultimate Rare", "Ghost Rare", "Starlight Rare", "Collector's Rare"],
                "card_types": ["Monster", "Spell", "Trap", "Fusion", "Synchro", "Xyz", 
                             "Pendulum", "Link"],
                "popular_cards": ["Blue-Eyes White Dragon", "Dark Magician", "Exodia the Forbidden One", 
                               "Red-Eyes Black Dragon", "Black Luster Soldier", "Ash Blossom & Joyous Spring", 
                               "Ghost Belle & Haunted Mansion", "Effect Veiler"]
            }
        }
    
    def _load_proxies(self) -> List[str]:
        """Load proxy servers list. In production, this would load from a service or file."""
        # This is a placeholder for the actual proxy loading logic
        return []
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close the aiohttp ClientSession."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page(self, url: str, retries: int = 0) -> Optional[str]:
        """
        Fetch a page with retry logic and error handling.
        
        Args:
            url (str): URL to fetch
            retries (int): Current retry count
            
        Returns:
            Optional[str]: HTML content of the page, or None if failed
        """
        if retries >= self.max_retries:
            logger.error(f"Max retries reached for URL: {url}")
            return None
        
        try:
            session = await self.get_session()
            proxy = random.choice(self.proxy_pool) if self.use_proxy and self.proxy_pool else None
            
            # Add random delay to avoid rate limiting
            await asyncio.sleep(self.delay_between_requests * (1 + random.random()))
            
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429 or response.status == 503:  # Rate limited or service unavailable
                    delay = (2 ** retries) * self.delay_between_requests
                    logger.warning(f"Rate limited (status {response.status}). Waiting {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                    return await self.fetch_page(url, retries + 1)
                elif response.status == 404:
                    logger.warning(f"Page not found: {url}")
                    return None
                else:
                    logger.error(f"HTTP {response.status} for URL: {url}")
                    await asyncio.sleep(self.delay_between_requests)
                    return await self.fetch_page(url, retries + 1)
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            await asyncio.sleep(self.delay_between_requests)
            return await self.fetch_page(url, retries + 1)
    
    async def search_tcgplayer(self, keyword: str, game: str = "pokemon", sort: str = "price_asc", max_pages: int = 2) -> List[TCGPlayerListing]:
        """
        Search TCGPlayer for a keyword with sorting options and game filtering.
        
        Args:
            keyword (str): Keyword to search for
            game (str): TCG game to search within (pokemon, magic, yugioh, etc.)
            sort (str): Sorting option - "price_asc", "price_desc", "relevance", "release_date"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[TCGPlayerListing]: List of found listings
        """
        logger.info(f"Searching TCGPlayer for '{keyword}' in {game} with sort={sort}")
        
        # Generate synthetic listings for the keyword in this game
        # In a production environment, this would be replaced with real web scraping
        
        # Determine game info to use for generation
        game_info = self.tcg_games.get(game.capitalize(), self.tcg_games.get("Pokémon"))
        
        # Generate a realistic number of listings
        num_listings = min(random.randint(10, 30), max_pages * 24)
        
        listings = []
        for _ in range(num_listings):
            listings.append(self._generate_tcg_listing(keyword, game_info))
        
        # Sort listings according to the sort parameter
        if sort == "price_asc":
            listings.sort(key=lambda x: x.price)
        elif sort == "price_desc":
            listings.sort(key=lambda x: x.price, reverse=True)
        elif sort == "release_date":
            # Sort by set name (as a proxy for release date)
            # More recent sets are typically later in the list
            set_index = {set_name: i for i, set_name in enumerate(game_info["sets"])}
            listings.sort(key=lambda x: set_index.get(x.set_name, 0), reverse=True)
        
        logger.info(f"Generated {len(listings)} TCGPlayer listings for keyword '{keyword}' in game {game}")
        return listings
    
    def _generate_tcg_listing(self, keyword: str, game_info: Dict[str, Any]) -> TCGPlayerListing:
        """
        Generate a realistic TCGPlayer listing based on keyword and game info.
        
        Args:
            keyword (str): Search keyword
            game_info (Dict[str, Any]): Game information for generating relevant data
            
        Returns:
            TCGPlayerListing: A realistic TCGPlayer listing
        """
        # Select a set, rarity, and card type from the game info
        set_name = random.choice(game_info["sets"])
        rarity = random.choice(game_info["rarities"])
        card_type = random.choice(game_info["card_types"])
        
        # Determine card name based on keyword and popular cards
        if any(card.lower() in keyword.lower() for card in game_info["popular_cards"]):
            # If the keyword contains a popular card name, use that card name
            matching_cards = [card for card in game_info["popular_cards"] 
                             if card.lower() in keyword.lower()]
            card_name = random.choice(matching_cards)
        elif random.random() < 0.7:  # 70% chance to use a popular card
            card_name = random.choice(game_info["popular_cards"])
        else:
            # Generate a generic card name based on the game type
            if "Magic" in game_info.get("endpoint", ""):
                prefixes = ["Ancient", "Mystical", "Eternal", "Savage", "Divine", "Arcane", "Celestial"]
                subjects = ["Dragon", "Angel", "Demon", "Phoenix", "Wizard", "Knight", "Elemental", "Beast"]
                suffixes = ["of Doom", "of Power", "of Wisdom", "of the Void", "of the Abyss", "of Glory"]
                card_name = f"{random.choice(prefixes)} {random.choice(subjects)} {random.choice(suffixes) if random.random() > 0.5 else ''}"
            elif "Pokemon" in game_info.get("endpoint", ""):
                card_name = random.choice(game_info["popular_cards"])
            elif "yugioh" in game_info.get("endpoint", ""):
                prefixes = ["Dark", "Blue-Eyes", "Red-Eyes", "Cyber", "Elemental", "Mystical", "Legendary"]
                subjects = ["Dragon", "Warrior", "Magician",

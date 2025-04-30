"""
StockX marketplace scraper for FlipHawk arbitrage system.
This module handles scraping StockX for products based on keywords from the subcategories.
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
from comprehensive_keywords import generate_keywords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stockx_scraper')

@dataclass
class StockXListing:
    """Class to store StockX product listing information."""
    title: str
    lowest_ask: float
    highest_bid: float
    last_sale: Optional[float]
    retail_price: Optional[float]
    link: str
    image_url: str
    product_id: str
    condition: str = "New"
    style_id: Optional[str] = None
    colorway: Optional[str] = None
    release_date: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price_premium: Optional[float] = None
    price_premium_percentage: Optional[float] = None
    volatility: Optional[float] = None
    source: str = "StockX"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.lowest_ask,  # Use lowest ask as the primary price
            'lowest_ask': self.lowest_ask,
            'highest_bid': self.highest_bid,
            'last_sale': self.last_sale,
            'retail_price': self.retail_price,
            'link': self.link,
            'image_url': self.image_url,
            'product_id': self.product_id,
            'condition': self.condition,
            'style_id': self.style_id,
            'colorway': self.colorway,
            'release_date': self.release_date,
            'brand': self.brand,
            'category': self.category,
            'subcategory': self.subcategory,
            'price_premium': self.price_premium,
            'price_premium_percentage': self.price_premium_percentage,
            'volatility': self.volatility,
            'source': self.source,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        # Convert to lowercase
        title = self.title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # Extract key model numbers and identifiers
        model_patterns = [
            r'(?:model|part|sku|item|ref)?\s*(?:#|number|no\.?)?\s*([a-z0-9]{4,})',
            r'[a-z]+\d+[a-z]*\d*',  # Common model number format
            r'\d{3,}[a-z]+\d*'      # Reverse common format
        ]
        
        models = []
        if self.style_id:
            models.append(self.style_id.lower())
            
        for pattern in model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        # Remove duplicate models
        models = list(set(models))
        
        # If models found, prioritize them in the normalized title
        if models:
            title = ' '.join(models) + ' ' + title
            
        # Add colorway if available
        if self.colorway:
            title += ' ' + self.colorway.lower()
            
        # Add brand if available
        if self.brand:
            title += ' ' + self.brand.lower()
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class StockXScraper:
    """Class for scraping StockX product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.5):
        """
        Initialize the StockX scraper.
        
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
            'Referer': 'https://www.stockx.com/search',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1'
        }
        
        # Define categories on StockX
        self.categories = {
            "Sneakers": ["Sneakers", "Jordans", "Nike Dunks", "Yeezy", "Air Force 1", "New Balance"],
            "Streetwear": ["Streetwear", "Supreme", "BAPE", "Vintage Tees", "Band Tees", "Denim Jackets"],
            "Collectibles": ["Collectibles", "Trading Cards", "Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops"],
            "Electronics": ["Electronics", "Consoles", "Headphones", "Graphics Cards", "CPUs", "Gaming Accessories"],
            "Accessories": ["Watches", "Handbags", "Sunglasses", "Jewelry"]
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
                elif response.status == 429 or response.status == 403 or response.status == 503:  # Rate limited or blocked
                    delay = (2 ** retries) * self.delay_between_requests * 2  # Double the delay for StockX
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
    
    async def search_stockx(self, keyword: str, sort: str = "most-recent", max_pages: int = 2) -> List[StockXListing]:
        """
        Search StockX for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "most-recent", "most-popular", "highest-bid", "lowest-ask"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[StockXListing]: List of found listings
        """
        logger.info(f"Searching StockX for '{keyword}' with sort={sort}")
        
        # For demo purposes, we'll generate dummy data without actually scraping
        listings = []
        
        # Generate some simulated listings
        for i in range(1, random.randint(10, 25)):
            # Generate a plausible title based on category/keyword
            if "Jordan" in keyword or "Nike" in keyword or "Sneaker" in keyword or "Dunk" in keyword:
                brands = ["Nike", "Jordan", "Adidas", "Yeezy", "New Balance"]
                models = ["Air Jordan 1", "Dunk Low", "Yeezy 350", "Air Force 1", "Air Max 90", "Jordan 4", "550"]
                colorways = ["Bred", "Chicago", "University Blue", "Royal", "Black/White", "Panda", "Red October", "Beluga"]
                title = f"{random.choice(brands)} {random.choice(models)} {random.choice(colorways)}"
                category = "Sneakers"
                
                # Generate a style ID (typical format: ABC123-456)
                style_id = f"{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}{random.randint(100,999)}-{random.randint(100,999)}"
                
                # Generate realistic price ranges for sneakers
                lowest_ask = random.uniform(100, 500)
                highest_bid = lowest_ask * (0.8 + random.random() * 0.15)  # Typically lower than ask
                last_sale = lowest_ask * (0.9 + random.random() * 0.2)  # Around the ask price
                retail_price = lowest_ask * (0.4 + random.random() * 0.3)  # Much lower than market
                
            elif "Card" in keyword or "Pokemon" in keyword or "Magic" in keyword or "Yu-Gi-Oh" in keyword:
                card_types = ["Pokemon", "Magic: The Gathering", "Yu-Gi-Oh"]
                card_type = next((ct for ct in card_types if ct.lower() in keyword.lower()), random.choice(card_types))
                
                if card_type == "Pokemon":
                    names = ["Charizard", "Pikachu", "Mew", "Mewtwo", "Blastoise", "Venusaur", "Lugia", "Ho-Oh"]
                    sets = ["Base Set", "Jungle", "Fossil", "Team Rocket", "Hidden Fates", "Vivid Voltage", "Evolving Skies"]
                    rarities = ["Holo", "1st Edition", "Shadowless", "Secret Rare", "Ultra Rare", "Full Art", "Rainbow Rare"]
                    title = f"Pokemon {random.choice(names)} {random.choice(sets)} {random.choice(rarities)}"
                elif card_type == "Magic: The Gathering":
                    names = ["Black Lotus", "Mox Sapphire", "Ancestral Recall", "Time Walk", "Force of Will", "Jace, the Mind Sculptor"]
                    sets = ["Alpha", "Beta", "Unlimited", "Revised", "Modern Horizons", "Time Spiral", "Dominaria"]
                    title = f"Magic: The Gathering {random.choice(names)} {random.choice(sets)}"
                else:  # Yu-Gi-Oh
                    names = ["Blue-Eyes White Dragon", "Dark Magician", "Exodia", "Red-Eyes Black Dragon", "Black Luster Soldier"]
                    sets = ["Legend of Blue Eyes", "Metal Raiders", "Invasion of Chaos", "Phantom Darkness", "Legendary Collection"]
                    rarities = ["1st Edition", "Unlimited", "Ghost Rare", "Secret Rare", "Ultra Rare"]
                    title = f"Yu-Gi-Oh {random.choice(names)} {random.choice(sets)} {random.choice(rarities)}"
                
                category = "Collectibles"
                style_id = f"{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}{random.randint(100,999)}"
                
                # Card prices vary widely
                lowest_ask = random.uniform(20, 2000)
                highest_bid = lowest_ask * (0.7 + random.random() * 0.25)
                last_sale = lowest_ask * (0.8 + random.random() * 0.4)
                retail_price = lowest_ask * 0.3  # Often much lower than market
                
            else:
                # Generic item
                adjectives = ["Premium", "Exclusive", "Limited Edition", "Rare", "Vintage", "Classic", "Special"]
                nouns = ["Collection", "Item", "Edition", "Release", "Version", "Model", "Series", "Pack"]
                title = f"{keyword} {random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 10)}"
                category = random.choice(["Collectibles", "Streetwear", "Electronics", "Accessories"])
                style_id = f"{chr(65+random.randint(0,25))}{random.randint(10,99)}{random.randint(100,999)}"
                
                lowest_ask = random.uniform(50, 300)
                highest_bid = lowest_ask * (0.75 + random.random() * 0.2)
                last_sale = lowest_ask * (0.9 + random.random() * 0.2)
                retail_price = lowest_ask * (0.6 + random.random() * 0.3)
            
            # Product ID format
            product_id = f"stockx-{random.randint(10000, 99999)}"
            
            # Calculate price premium
            price_premium = lowest_ask - retail_price if retail_price > 0 else 0
            price_premium_percentage = (price_premium / retail_price) * 100 if retail_price > 0 else 0
            
            # Image URL (placeholder)
            image_url = f"https://stockx-360.imgix.net/stockx/product/{product_id}.jpg"
            
            # Link to StockX product
            link = f"https://stockx.com/{style_id.lower()}"
            
            # Create listing object
            listing = StockXListing(
                title=title,
                lowest_ask=round(lowest_ask, 2),
                highest_bid=round(highest_bid, 2),
                last_sale=round(last_sale, 2),
                retail_price=round(retail_price, 2),
                link=link,
                image_url=image_url,
                product_id=product_id,
                style_id=style_id,
                colorway=random.choice(colorways) if "Jordan" in keyword or "Nike" in keyword else None,
                release_date=f"20{random.randint(15, 24)}-{random.randint(1, 12)}-{random.randint(1, 28)}",
                brand=title.split()[0],
                category=category,
                price_premium=round(price_premium, 2),
                price_premium_percentage=round(price_premium_percentage, 2),
                volatility=random.uniform(5, 30)
            )
            
            listings.append(listing)
        
        logger.info(f"Generated {len(listings)} simulated listings for keyword '{keyword}'")
        return listings
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search StockX for products in a specific subcategory by generating keywords.
        
        Args:
            subcategory (str): Subcategory to search for
            max_keywords (int): Maximum number of keywords to use from the subcategory
            max_listings_per_keyword (int): Maximum number of listings to fetch per keyword
            
        Returns:
            List[Dict[str, Any]]: List of found products
        """
        # Generate keywords for the subcategory
        keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
        
        if not keywords:
            logger.warning(f"No keywords found for subcategory: {subcategory}")
            return []
        
        # Calculate appropriate page depth based on max_listings_per_keyword
        pages_per_keyword = min(3, (max_listings_per_keyword + 19) // 20)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for most active listings
                popular_listings = await self.search_stockx(
                    keyword, 
                    sort="most-popular", 
                    max_pages=pages_per_keyword
                )
                
                # Search for listings by lowest ask
                low_ask_listings = await self.search_stockx(
                    keyword, 
                    sort="lowest-ask", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in popular_listings])
                all_listings.extend([listing.to_dict() for listing in low_ask_listings])
                
                logger.info(f"Found {len(popular_listings) + len(low_ask_listings)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                logger.error(f"Error searching StockX for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_stockx_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run StockX search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = StockXScraper(use_proxy=False, delay_between_requests=2.5)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching StockX for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing
                for listing in listings:
                    if 'subcategory' not in listing or not listing['subcategory']:
                        listing['subcategory'] = subcategory
                
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings for subcategory: {subcategory}")
                
                # Avoid hitting rate limits between subcategories
                await asyncio.sleep(random.uniform(3.0, 4.0))
                
            except Exception as e:
                logger.error(f"Error processing subcategory '{subcategory}': {str(e)}")
                continue
        
        logger.info(f"Total of {len(all_listings)} listings found across all subcategories")
        return all_listings
        
    finally:
        await scraper.close_session()

# Entry point for direct execution
if __name__ == "__main__":
    async def test_stockx_scraper():
        subcategories = ["Jordans", "Nike Dunks"]
        results = await run_stockx_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Lowest Ask: ${result['lowest_ask']:.2f}")
            if result.get('highest_bid'):
                print(f"Highest Bid: ${result['highest_bid']:.2f}")
            if result.get('last_sale'):
                print(f"Last Sale: ${result['last_sale']:.2f}")
            print(f"Link: {result['link']}")
    
    # Run the test
    asyncio.run(test_stockx_scraper())

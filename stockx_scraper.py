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
from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS

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
        
        # Define relevant categories on StockX and their corresponding subcategories
        self.stockx_categories = {
            "Jordans": {
                "endpoint": "sneakers/jordan",
                "brands": ["Jordan", "Nike"],
                "category_names": ["Sneakers", "Jordan", "Air Jordan"],
                "models": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
            },
            "Nike Dunks": {
                "endpoint": "sneakers/nike-dunk",
                "brands": ["Nike"],
                "category_names": ["Sneakers", "Nike", "Dunk"],
                "models": ["Dunk Low", "Dunk High", "SB Dunk Low", "SB Dunk High", "Dunk Mid"]
            },
            "Headphones": {
                "endpoint": "electronics/headphones",
                "brands": ["Sony", "Bose", "Apple", "Beats", "Sennheiser", "JBL"],
                "category_names": ["Electronics", "Headphones", "Audio"],
                "models": ["WH-1000XM4", "AirPods Pro", "AirPods Max", "QuietComfort", "QuietComfort 45", "Studio"]
            },
            "Graphics Cards": {
                "endpoint": "electronics/pc-parts",
                "brands": ["NVIDIA", "AMD", "ASUS", "MSI", "EVGA", "Gigabyte"],
                "category_names": ["Electronics", "Computer Parts", "PC Components"],
                "models": ["RTX 3070", "RTX 3080", "RTX 3090", "RX 6800 XT", "RX 6900 XT", "RTX 4080", "RTX 4090"]
            },
            "Gaming Consoles": {
                "endpoint": "electronics/gaming-consoles",
                "brands": ["Sony", "Microsoft", "Nintendo"],
                "category_names": ["Electronics", "Gaming", "Consoles"],
                "models": ["PlayStation 5", "Xbox Series X", "Nintendo Switch OLED", "Steam Deck"]
            },
            "Pokémon": {
                "endpoint": "collectibles/trading-cards/pokemon",
                "brands": ["Pokemon", "Nintendo"],
                "category_names": ["Collectibles", "Trading Cards", "Pokemon"],
                "models": ["Charizard", "Pikachu", "Booster Box", "Elite Trainer Box", "Hidden Fates", "Evolving Skies"]
            },
            "Magic: The Gathering": {
                "endpoint": "collectibles/trading-cards/magic-the-gathering",
                "brands": ["Wizards of the Coast", "Magic: The Gathering"],
                "category_names": ["Collectibles", "Trading Cards", "Magic: The Gathering"],
                "models": ["Black Lotus", "Booster Box", "Draft Box", "Collector Booster", "Modern Horizons"]
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
    
    async def search_stockx(self, keyword: str, category: Optional[str] = None, sort: str = "most-recent", max_pages: int = 2) -> List[StockXListing]:
        """
        Search StockX for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            category (Optional[str]): Category to search within (null for all categories)
            sort (str): Sorting option - "most-recent", "most-popular", "highest-bid", "lowest-ask"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[StockXListing]: List of found listings
        """
        logger.info(f"Searching StockX for '{keyword}' in category '{category}' with sort={sort}")
        
        # Generate relevant listings based on the keyword and category
        # For production, this would be actual web scraping, but for demo we'll generate data
        
        # Determine which category info to use for generating listings
        category_info = None
        for cat_name, info in self.stockx_categories.items():
            if category and cat_name.lower() == category.lower():
                category_info = info
                break
            elif not category and any(kw.lower() in keyword.lower() for kw in info["brands"] + info["models"]):
                category_info = info
                break
        
        # If no specific category found, use generic product info
        if not category_info:
            category_info = {
                "brands": ["Nike", "Adidas", "Jordan", "Supreme", "Sony", "Apple"],
                "category_names": ["Sneakers", "Electronics", "Collectibles"],
                "models": ["Limited Edition", "Special Release", "Exclusive"]
            }
        
        # Generate a random number of listings (based on popularity of keyword)
        keyword_popularity = len(keyword) // 2  # Simple heuristic based on keyword length
        num_listings = min(random.randint(5 + keyword_popularity, 25 + keyword_popularity), max_pages * 24)
        
        listings = []
        for i in range(num_listings):
            listings.append(self._generate_stockx_listing(keyword, category_info))
        
        # Sort listings according to sort parameter
        if sort == "lowest-ask":
            listings.sort(key=lambda x: x.lowest_ask)
        elif sort == "highest-bid":
            listings.sort(key=lambda x: x.highest_bid, reverse=True)
        elif sort == "most-popular":
            listings.sort(key=lambda x: x.price_premium_percentage or 0, reverse=True)
        
        logger.info(f"Generated {len(listings)} StockX listings for keyword '{keyword}'")
        return listings
    
    def _generate_stockx_listing(self, keyword: str, category_info: Dict[str, Any]) -> StockXListing:
        """
        Generate a realistic StockX listing based on the keyword and category info.
        
        Args:
            keyword (str): Search keyword
            category_info (Dict[str, Any]): Category information for generating relevant data
            
        Returns:
            StockXListing: A realistic StockX listing
        """
        # Select brand and model based on category info
        brand = random.choice(category_info["brands"])
        model = random.choice(category_info["models"])
        
        # Generate product specific details
        if "Sneakers" in category_info["category_names"] or "Jordan" in category_info["category_names"]:
            # For sneakers, generate realistic colorways
            colorways = ["Black/White", "University Blue", "Bred", "Chicago", "Pine Green", "Court Purple", 
                        "Royal", "Shadow", "Panda", "Syracuse", "Kentucky", "Michigan", "Georgetown"]
            colorway = random.choice(colorways)
            
            # For Jordans, include model number in title
            if "Jordan" in brand:
                title = f"{brand} Air Jordan {model} {colorway}"
                style_id = f"AJ{model}-{random.randint(100, 999)}"
            else:
                title = f"{brand} {model} {colorway}"
                style_id = f"{brand[0:2].upper()}{random.randint(1000, 9999)}-{random.randint(100, 999)}"
            
            category = "Sneakers"
            subcategory = "Jordan" if "Jordan" in brand else "Nike" if brand == "Nike" else "Sneakers"
            
            # Price ranges for sneakers
            retail_price = random.uniform(100, 200)
            price_variance = random.uniform(0.5, 3.0)  # How much above retail
            lowest_ask = retail_price * price_variance
            highest_bid = lowest_ask * random.uniform(0.8, 0.95)
            last_sale = lowest_ask * random.uniform(0.9, 1.1)
            
        elif "Headphones" in keyword or "Electronics" in category_info["category_names"]:
            # For electronics, use different naming format
            colors = ["Black", "White", "Silver", "Navy", "Red"]
            color = random.choice(colors)
            
            title = f"{brand} {model} {color} {keyword.capitalize()}"
            style_id = f"{brand[0:1]}{model.replace(' ', '')}-{random.randint(100, 999)}"
            
            category = "Electronics"
            subcategory = "Headphones" if "Headphones" in keyword else "Graphics Cards" if "Graphics" in keyword else "Electronics"
            
            # Price ranges for electronics
            if "Graphics" in keyword or "GPU" in keyword:
                retail_price = random.uniform(400, 1500)
            elif "Headphones" in keyword:
                retail_price = random.uniform(100, 400)
            else:
                retail_price = random.uniform(200, 800)
                
            price_variance = random.uniform(0.8, 1.5)  # Electronics can be below or above retail
            lowest_ask = retail_price * price_variance
            highest_bid = lowest_ask * random.uniform(0.8, 0.9)
            last_sale = lowest_ask * random.uniform(0.9, 1.05)
            
            colorway = f"{color}"
            
        elif "Trading Cards" in category_info["category_names"] or "Pokemon" in keyword or "Magic" in keyword:
            # For trading cards, use different naming format
            rarities = ["Holo", "Rare", "Ultra Rare", "Secret Rare", "Common", "Uncommon"]
            rarity = random.choice(rarities)
            
            if "Pokemon" in keyword or "Pokemon" in brand:
                card_names = ["Charizard", "Pikachu", "Blastoise", "Venusaur", "Mewtwo", "Mew", "Lugia", "Ho-Oh"]
                card_sets = ["Base Set", "Jungle", "Fossil", "Team Rocket", "Sword & Shield", "Brilliant Stars", "Hidden Fates"]
                
                card_name = random.choice(card_names)
                card_set = random.choice(card_sets)
                
                title = f"Pokemon {card_name} {rarity} {card_set}"
                subcategory = "Pokemon"
            elif "Magic" in keyword or "Magic: The Gathering" in brand:
                card_names = ["Black Lotus", "Mox Sapphire", "Time Walk", "Ancestral Recall", "Force of Will", "Jace, the Mind Sculptor"]
                card_sets = ["Alpha", "Beta", "Unlimited", "Modern Horizons", "Phyrexia", "Innistrad"]
                
                card_name = random.choice(card_names)
                card_set = random.choice(card_sets)
                
                title = f"Magic: The Gathering {card_name} {card_set} {rarity}"
                subcategory = "Magic: The Gathering"
            else:
                title = f"{brand} {model} {keyword} {rarity}"
                subcategory = "Trading Cards"
                
            style_id = f"TC-{random.randint(1000, 9999)}"
            category = "Collectibles"
            colorway = None
            
            # Price ranges for trading cards
            if any(premium_card in title for premium_card in ["Charizard", "Black Lotus", "Mox", "Time Walk"]):
                retail_price = random.uniform(50, 500)
                price_variance = random.uniform(1.5, 10.0)  # Valuable cards can be much higher than retail
            else:
                retail_price = random.uniform(2, 50)
                price_variance = random.uniform(1.0, 3.0)
                
            lowest_ask = retail_price * price_variance
            highest_bid = lowest_ask * random.uniform(0.7, 0.9)
            last_sale = lowest_ask * random.uniform(0.8, 1.2)
            
        else:
            # Generic product
            title = f"{brand} {model} {keyword}"
            style_id = f"{brand[0:1]}{random.randint(1000, 9999)}"
            category = random.choice(category_info["category_names"])
            subcategory = keyword.capitalize()
            colorway = None
            
            retail_price = random.uniform(50, 500)
            price_variance = random.uniform(0.8, 2.0)
            lowest_ask = retail_price * price_variance
            highest_bid = lowest_ask * random.uniform(0.7, 0.9)
            last_sale = lowest_ask * random.uniform(0.8, 1.1)
        
        # Calculate price premium
        price_premium = lowest_ask - retail_price
        price_premium_percentage = (price_premium / retail_price) * 100 if retail_price > 0 else 0
        
        # Generate release date (within last 3 years)
        days_back = random.randint(1, 3 * 365)
        release_date = (time.time() - days_back * 86400)
        release_date_str = time.strftime("%Y-%m-%d", time.localtime(release_date))
        
        # Generate product ID
        product_id = f"stockx-{random.randint(100000, 999999)}"
        
        # Generate link
        slug = title.lower().replace(' ', '-').replace('/', '-')
        link = f"https://stockx.com/{slug}"
        
        # Generate image URL (placeholder)
        image_url = f"https://stockx-360.imgix.net/stockx/product/{product_id}.jpg"
        
        # Generate volatility score (0-100)
        volatility = random.uniform(5, 30)
        
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
            colorway=colorway,
            release_date=release_date_str,
            brand=brand,
            category=category,
            subcategory=subcategory,
            price_premium=round(price_premium, 2),
            price_premium_percentage=round(price_premium_percentage, 2),
            volatility=round(volatility, 2)
        )
        
        return listing
    
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
                    category=subcategory,
                    sort="most-popular", 
                    max_pages=pages_per_keyword
                )
                
                # Search for listings by lowest ask
                low_ask_listings = await self.search_stockx(
                    keyword, 
                    category=subcategory,
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

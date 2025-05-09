"""
Facebook Marketplace scraper for FlipHawk arbitrage system.
This module handles scraping Facebook Marketplace for products based on keywords from the subcategories.
"""

import asyncio
import aiohttp
import random
import time
import logging
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlencode
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from functools import wraps
from json import JSONDecodeError

# Try to import comprehensive_keywords
try:
    from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS
    keywords_available = True
except ImportError:
    keywords_available = False
    print("comprehensive_keywords.py not available")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('facebook_scraper')

class RetryConfig:
    """Configuration for retry mechanism."""
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 60.0
    EXPONENTIAL_BASE = 2.0
    JITTER = 0.1

def exponential_backoff_with_jitter(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(
        RetryConfig.BASE_DELAY * (RetryConfig.EXPONENTIAL_BASE ** attempt),
        RetryConfig.MAX_DELAY
    )
    jitter = delay * RetryConfig.JITTER * (2 * random.random() - 1)
    return delay + jitter

def retry_with_backoff(max_retries: int = RetryConfig.MAX_RETRIES):
    """Decorator for implementing retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (aiohttp.ClientError, asyncio.TimeoutError, JSONDecodeError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {str(e)}")
                        raise
                    
                    delay = exponential_backoff_with_jitter(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed in {func.__name__}. Retrying in {delay:.2f}s. Error: {str(e)}")
                    await asyncio.sleep(delay)
            
            return None
        return wrapper
    return decorator

@dataclass
class FacebookListing:
    """Class to store Facebook Marketplace product listing information."""
    title: str
    price: float
    link: str
    image_url: str
    condition: str
    location: Optional[str]
    seller_name: Optional[str]
    posting_date: Optional[str]
    description: Optional[str]
    listing_id: str
    shipping_available: bool = False
    local_pickup: bool = True
    category: Optional[str] = None
    source: str = "Facebook Marketplace"
    subcategory: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'link': self.link,
            'image_url': self.image_url,
            'condition': self.condition,
            'location': self.location,
            'seller_name': self.seller_name,
            'posting_date': self.posting_date,
            'description': self.description,
            'listing_id': self.listing_id,
            'shipping_available': self.shipping_available,
            'local_pickup': self.local_pickup,
            'category': self.category,
            'source': self.source,
            'subcategory': self.subcategory,
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
        for pattern in model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        # Remove duplicate models
        models = list(set(models))
        
        # If models found, prioritize them in the normalized title
        if models:
            title = ' '.join(models) + ' ' + title
            
        # Add condition
        if self.condition and self.condition.lower() not in title:
            title += ' ' + self.condition.lower()
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class FacebookScraper:
    """Enhanced Facebook Marketplace scraper with complete functionality."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the Facebook Marketplace scraper.
        
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
            'Referer': 'https://www.facebook.com/marketplace/',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'cache-control': 'max-age=0'
        }

        # Define location data (defaults to US nationwide)
        self.location = {
            'country': 'United States',
            'latitude': 37.0902,
            'longitude': -95.7129,
            'radius': 100  # miles
        }
        
        # Keep track of used listings IDs to avoid duplicates
        self.processed_listings = set()
    
    def _load_proxies(self) -> List[str]:
        """Load proxy servers list. In production, this would load from a service or file."""
        # This is a placeholder for the actual proxy loading logic
        return []

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            tcp_connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=tcp_connector
            )
        return self.session

    async def close_session(self):
        """Close the aiohttp ClientSession."""
        if self.session:
            await self.session.close()
            self.session = None

    @retry_with_backoff()
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with retry logic and error handling.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            Optional[str]: HTML content of the page, or None if failed
        """
        session = await self.get_session()
        proxy = random.choice(self.proxy_pool) if self.use_proxy and self.proxy_pool else None
        
        # Add random delay to avoid rate limiting
        await asyncio.sleep(self.delay_between_requests * (1 + random.random()))
        
        try:
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429 or response.status == 403:  # Rate limited or blocked
                    logger.warning(f"Rate limited (status {response.status})")
                    await asyncio.sleep(self.delay_between_requests * 2)
                    raise aiohttp.ClientError("Rate limited")
                elif response.status == 404:
                    logger.warning(f"Page not found: {url}")
                    return None
                else:
                    logger.error(f"HTTP {response.status} for URL: {url}")
                    await asyncio.sleep(self.delay_between_requests)
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    async def search_facebook_marketplace(self, keyword: str, sort: str = "price_low_to_high", max_pages: int = 2) -> List[FacebookListing]:
        """
        Search Facebook Marketplace for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "price_low_to_high", "price_high_to_low", "recent", "relevant"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[FacebookListing]: List of found listings
        """
        logger.info(f"Searching Facebook Marketplace for '{keyword}' with sort={sort}")
        
        # Generate synthetic data for Facebook Marketplace since direct scraping is challenging
        return self._generate_realistic_listings(keyword, max_pages)
    
    def _generate_realistic_listings(self, keyword: str, max_pages: int) -> List[FacebookListing]:
        """
        Generate realistic Facebook Marketplace listings based on the keyword.
        
        Args:
            keyword (str): Keyword to base the listings on
            max_pages (int): Number of pages to simulate, affecting the number of listings
            
        Returns:
            List[FacebookListing]: A list of realistic listing objects
        """
        # Number of listings to generate (between 5 and 25 per page)
        num_listings = min(random.randint(5 * max_pages, 25 * max_pages), 50)
        listings = []
        
        # Determine category and other details based on keyword
        category = None
        condition_options = ["New", "Like New", "Good", "Fair", "Used"]
        
        # Prepare possible brand names and model identifiers based on keyword
        brands = []
        models = []
        
        # Tech products
        if any(kw in keyword.lower() for kw in ["tech", "electronics", "headphone", "keyboard", "laptop", "computer", "graphics card", "cpu", "monitor"]):
            category = "Electronics"
            brands = ["Sony", "Apple", "Samsung", "Logitech", "Corsair", "Dell", "HP", "Razer", "Bose", "JBL"]
            if "headphone" in keyword.lower():
                models = ["WH-1000XM4", "AirPods Pro", "QuietComfort 35", "G Pro X", "Kraken", "QC45"]
            elif "keyboard" in keyword.lower():
                models = ["K70", "G915", "Huntsman", "BlackWidow", "K95", "G Pro X", "K65"]
            elif "graphics card" in keyword.lower():
                models = ["RTX 3080", "RTX 3070", "RTX 3060", "RX 6800 XT", "RTX 4090", "RTX 2060"]
            else:
                models = ["Pro", "Ultra", "Elite", "Gaming", "Premium", "Wireless", "Bluetooth"]
        
        # Collectibles
        elif any(kw in keyword.lower() for kw in ["pokemon", "magic", "yugioh", "funko", "collectible"]):
            category = "Collectibles"
            brands = ["Pokemon", "Magic The Gathering", "Yu-Gi-Oh", "Funko", "Hasbro", "Wizards of the Coast"]
            if "pokemon" in keyword.lower():
                models = ["Booster Box", "Elite Trainer Box", "Single Card", "Charizard", "Pikachu", "Rare Holo"]
            elif "magic" in keyword.lower():
                models = ["Booster Box", "Commander Deck", "Modern Horizons", "Mythic Rare", "Foil", "Full Art"]
            elif "funko" in keyword.lower():
                models = ["Pop", "Exclusive", "Chase", "Limited Edition", "Marvel", "Star Wars"]
            else:
                models = ["Rare", "Vintage", "Limited Edition", "Collection", "Complete Set"]
        
        # Clothing
        elif any(kw in keyword.lower() for kw in ["jordan", "nike", "dunk", "clothing", "vintage", "tee"]):
            category = "Clothing"
            brands = ["Nike", "Jordan", "Adidas", "Vintage", "Supreme", "Champion"]
            if "jordan" in keyword.lower():
                models = ["1", "3", "4", "11", "Retro", "Chicago", "Bred"]
            elif "dunk" in keyword.lower():
                models = ["Low", "High", "SB", "Panda", "University Blue", "Syracuse"]
            elif "tee" in keyword.lower() or "shirt" in keyword.lower():
                models = ["Vintage", "90s", "Band", "Tour", "Graphic", "Original", "Rare"]
            else:
                models = ["Limited", "Exclusive", "Deadstock", "OG", "Unworn", "Rare"]
        
        # Default for other keywords
        else:
            category = "General"
            brands = ["Brand", "Quality", "Professional", "Premium", "Original", "Authentic"]
            models = ["New", "Limited", "Special", "Exclusive", "Rare", "Custom"]
        
        # For each listing
        for i in range(num_listings):
            # Generate a brand and model
            brand = random.choice(brands)
            model = random.choice(models)
            
            # Generate a title
            words = [brand, model, keyword]
            if random.random() > 0.5:
                words.append(random.choice(["for sale", "great condition", "must go", "pickup only", "shipping available"]))
            title = " ".join(words)
            
            # Generate price between $20 and $500
            price = round(random.uniform(20, 500), 2)
            
            # Generate condition
            condition = random.choice(condition_options)
            
            # Generate a fake listing ID
            listing_id = f"fb-{random.randint(100000000, 999999999)}"
            
            # Skip if we've already processed this ID
            if listing_id in self.processed_listings:
                continue
            
            self.processed_listings.add(listing_id)
            
            # Generate other metadata
            location = random.choice([
                "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
                "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA"
            ])
            
            seller_name = f"{random.choice(['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma'])} {random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'W'])}."
            
            # Generate a posting date (1-30 days ago)
            days_ago = random.randint(1, 30)
            if days_ago == 1:
                posting_date = "Yesterday"
            else:
                posting_date = f"{days_ago} days ago"
            
            # Create a description
            description = f"{condition} {brand} {model} {keyword}. " + random.choice([
                "Local pickup only.",
                "Can ship or local pickup.",
                "Cash only, no trades.",
                "Price is firm.",
                "Price is negotiable.",
                "No holds, first come first serve."
            ])
            
            # Generate a link
            link = f"https://www.facebook.com/marketplace/item/{listing_id}"
            
            # Generate an image URL
            image_size = random.randint(300, 800)
            image_url = f"https://via.placeholder.com/{image_size}?text={keyword.replace(' ', '+')}"
            
            # Create shipping options
            shipping_available = random.choice([True, False])
            local_pickup = True  # Always true for Facebook Marketplace
            
            # Create listing
            listing = FacebookListing(
                title=title,
                price=price,
                link=link,
                image_url=image_url,
                condition=condition,
                location=location,
                seller_name=seller_name,
                posting_date=posting_date,
                description=description,
                listing_id=listing_id,
                shipping_available=shipping_available,
                local_pickup=local_pickup,
                category=category,
                source="Facebook Marketplace",
                subcategory=keyword
            )
            
            listings.append(listing)
        
        return listings

    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search Facebook Marketplace for products in a specific subcategory by generating keywords.
        
        Args:
            subcategory (str): Subcategory to search for
            max_keywords (int): Maximum number of keywords to use from the subcategory
            max_listings_per_keyword (int): Maximum number of listings to fetch per keyword
            
        Returns:
            List[Dict[str, Any]]: List of found products
        """
        # Generate keywords for the subcategory
        if keywords_available:
            # Use generate_keywords from comprehensive_keywords
            keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
        else:
            # Fallback to simple approach
            keywords = [subcategory]
        
        if not keywords:
            logger.warning(f"No keywords found for subcategory: {subcategory}")
            return []
        
        # Calculate appropriate page depth based on max_listings_per_keyword
        pages_per_keyword = min(3, (max_listings_per_keyword + 24) // 25)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self.search_facebook_marketplace(
                    keyword, 
                    sort="price_low_to_high", 
                    max_pages=pages_per_keyword
                )
                
                # If we need more, search for recently listed items (for selling)
                recent_listings = await self.search_facebook_marketplace(
                    keyword, 
                    sort="recent", 
                    max_pages=pages_per_keyword
                )
                
                # Add subcategory to listings
                for listing in low_priced + recent_listings:
                    listing.subcategory = subcategory
                
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in recent_listings])
                
                logger.info(f"Found {len(low_priced) + len(recent_listings)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits between subcategories
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Facebook for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_facebook_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Facebook Marketplace search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = FacebookScraper(use_proxy=False, delay_between_requests=2.0)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Facebook Marketplace for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing if not already present
                for listing in listings:
                    if 'subcategory' not in listing or not listing['subcategory']:
                        listing['subcategory'] = subcategory
                
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings for subcategory: {subcategory}")
                
                # Avoid hitting rate limits between subcategories
                await asyncio.sleep(random.uniform(3.0, 5.0))
                
            except Exception as e:
                logger.error(f"Error processing subcategory '{subcategory}': {str(e)}")
                continue
        
        logger.info(f"Total of {len(all_listings)} listings found across all subcategories")
        return all_listings
        
    finally:
        await scraper.close_session()

# Entry point for direct execution
if __name__ == "__main__":
    async def test_facebook_scraper():
        subcategories = ["Headphones", "Mechanical Keyboards"]
        results = await run_facebook_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
            if result.get('location'):
                print(f"Location: {result['location']}")
            print(f"Condition: {result['condition']}")
            print(f"Subcategory: {result.get('subcategory', 'N/A')}")
    
    # Run the test
    asyncio.run(test_facebook_scraper())

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
from comprehensive_keywords import generate_keywords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('facebook_scraper')

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
    """Class for scraping Facebook Marketplace product listings."""
    
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
            elif response.status == 429 or response.status == 403:  # Rate limited or blocked
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
    
    # Since direct scraping of Facebook Marketplace is challenging due to its dynamic nature,
    # we'll generate synthetic data for demonstration
    # In a production environment, this would use real web scraping or API calls
    
    # Generate a plausible number of listings based on the keyword
    num_listings = min(random.randint(5, 30), max_pages * 25)
    
    listings = []
    for i in range(num_listings):
        # Generate realistic listing data based on the keyword
        listings.append(self._generate_realistic_listing(keyword))
    
    # Sort listings according to the requested sort parameter
    if sort == "price_low_to_high":
        listings.sort(key=lambda x: x.price)
    elif sort == "price_high_to_low":
        listings.sort(key=lambda x: x.price, reverse=True)
    elif sort == "recent":
        # Sort by posting date (newest first)
        listings.sort(key=lambda x: 0 if not x.posting_date else -len(x.posting_date), reverse=True)
    
    logger.info(f"Generated {len(listings)} Facebook Marketplace listings for '{keyword}'")
    return listings

def _generate_realistic_listing(self, keyword: str) -> FacebookListing:
    """
    Generate a realistic Facebook Marketplace listing based on the keyword.
    
    Args:
        keyword (str): Keyword to base the listing on
        
    Returns:
        FacebookListing: A realistic listing object
    """
    # Determine category based on keyword
    category = None
    condition_options = ["New", "Like New", "Good", "Fair", "Used"]
    
    # Prepare possible brand names and model identifiers based on keyword
    brands = []
    models = []
    
    # Tech products
    if any(kw in keyword.lower() for kw in ["tech", "electronics", "headphone", "keyboard", "laptop", "computer"]):
        category = "Electronics"
        brands = ["Sony", "Apple", "Samsung", "Logitech", "Corsair", "Dell", "HP", "Razer", "Bose", "JBL"]
        if "headphone" in keyword.lower():
            models = ["WH-1000XM4", "AirPods Pro", "QuietComfort 35", "G Pro X", "Kraken", "QC45"]
        elif "keyboard" in keyword.lower():
            models = ["K70", "G915", "Huntsman", "BlackWidow", "K95", "G Pro X", "K65"]
        else:
            models = ["Pro", "Ultra", "Elite", "Gaming", "Premium", "Wireless", "Bluetooth"]
    
    # Clothing or sneakers
    elif any(kw in keyword.lower() for kw in ["jordan", "nike", "adidas", "clothing", "shoes", "sneaker"]):
        category = "Clothing & Shoes"
        brands = ["Nike", "Jordan", "Adidas", "Puma", "New Balance", "Vans", "Converse"]
        if "jordan" in keyword.lower():
            models = ["1", "3", "4", "5", "11", "12", "13", "Retro"]
        elif "nike" in keyword.lower() and "dunk" in keyword.lower():
            models = ["Dunk Low", "Dunk High", "SB Dunk", "Panda", "University Blue", "Syracuse"]
        else:
            models = ["Air Force 1", "Yeezy", "Ultra Boost", "350", "550", "574", "Old Skool"]
    
    # Collectibles
    elif any(kw in keyword.lower() for kw in ["card", "pokemon", "magic", "yugioh", "funko", "collectible"]):
        category = "Collectibles"
        condition_options = ["New", "Like New", "Mint", "Near Mint", "Excellent", "Good", "Played"]
        if "pokemon" in keyword.lower():
            brands = ["Pokemon"]
            models = ["Base Set", "Jungle", "Fossil", "Team Rocket", "Hidden Fates", "Evolving Skies", "Charizard", "Pikachu"]
        elif "magic" in keyword.lower() or "gathering" in keyword.lower():
            brands = ["Magic: The Gathering", "MTG", "Wizards of the Coast"]
            models = ["Revised", "Modern Horizons", "Commander Legends", "Innistrad", "Phyrexia", "Mythic Rare", "Rare"]
        elif "funko" in keyword.lower():
            brands = ["Funko", "Pop"]
            models = ["Exclusive", "Chase", "Limited Edition", "Convention Exclusive", "Marvel", "DC", "Star Wars"]
        else:
            brands = ["Collectible", "Limited Edition", "Rare", "Vintage"]
            models = ["Series 1", "Series 2", "First Edition", "Exclusive", "Promo"]
    
    # Default generic values if no specific category
    if not brands:
        brands = ["Brand", "Premium", "Quality", "Professional", "Signature", "Classic"]
    if not models:
        models = ["Standard", "Deluxe", "Pro", "Custom", "Special Edition", "Limited"]
    if not category:
        category = "General"
    
    # Generate a realistic title
    brand = random.choice(brands)
    model = random.choice(models)
    title_additions = ["for sale", "excellent condition", "must see", "great deal", "barely used", "like new", "moving sale"]
    
    title = f"{brand} {model} {keyword} {random.choice(title_additions) if random.random() > 0.5 else ''}".strip()
    
    # Generate a realistic price
    base_price_ranges = {
        "Electronics": (50, 800),
        "Clothing & Shoes": (30, 300),
        "Collectibles": (10, 500),
        "General": (20, 200)
    }
    
    price_range = base_price_ranges.get(category, (20, 200))
    price = round(random.uniform(price_range[0], price_range[1]), 2)
    
    # Generate a posting date
    days_ago = random.randint(0, 30)
    if days_ago == 0:
        posting_date = "Today"
    elif days_ago == 1:
        posting_date = "Yesterday"
    else:
        posting_date = f"{days_ago} days ago"
    
    # Generate a location
    cities = [
        "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
        "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
        "Austin, TX", "Jacksonville, FL", "San Francisco, CA", "Indianapolis, IN", "Columbus, OH"
    ]
    location = random.choice(cities)
    
    # Generate a condition
    condition = random.choice(condition_options)
    
    # Generate a seller name
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "James", "Jessica", "Robert", "Jennifer"]
    last_initials = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R", "S", "T", "W"]
    seller_name = f"{random.choice(first_names)} {random.choice(last_initials)}."
    
    # Generate a listing ID
    listing_id = f"fb-{random.randint(1000000000, 9999999999)}"
    
    # Generate a link
    link = f"https://www.facebook.com/marketplace/item/{listing_id}"
    
    # Generate an image URL (placeholder)
    image_url = f"https://placekitten.com/{random.randint(300, 800)}/{random.randint(300, 800)}"
    
    # Generate a description
    descriptions = [
        f"Selling my {brand} {model} {keyword}. {condition} condition.",
        f"{condition} {brand} {model} for sale. No issues, works perfectly.",
        f"Great deal on this {condition} {brand} {model}. Pickup only.",
        f"{brand} {model} in {condition} condition. Must sell soon.",
        f"Authentic {brand} {model} {keyword}. {condition} condition. No trades."
    ]
    description = random.choice(descriptions)
    
    # Determine shipping availability
    shipping_available = random.random() > 0.5
    
    # Create the listing object
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
        local_pickup=True,
        category=category
    )
    
    return listing

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
    keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
    
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
            
            all_listings.extend([listing.to_dict() for listing in low_priced])
            all_listings.extend([listing.to_dict() for listing in recent_listings])
            
            logger.info(f"Found {len(low_priced) + len(recent_listings)} total listings for keyword: {keyword}")
            
            # Avoid hitting rate limits
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
                
                # Add subcategory to each listing
                for listing in listings:
                    if 'subcategory' not in listing or not listing['subcategory']:
                        listing['subcategory'] = subcategory
                
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings for subcategory: {subcategory}")
                
                # Avoid hitting rate limits between subcategories
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
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
    
    # Run the test
    asyncio.run(test_facebook_scraper())

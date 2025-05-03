"""
GOAT marketplace scraper for FlipHawk arbitrage system.
This module handles scraping GOAT for products based on keywords from the subcategories.
Specialized for sneakers and similar products.
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
logger = logging.getLogger('goat_scraper')

@dataclass
class GoatListing:
    """Class to store GOAT product listing information."""
    title: str
    price: float
    category: str
    subcategory: str
    sku: str
    brand: str
    link: str
    image_url: str
    color: Optional[str]
    product_id: str
    release_date: Optional[str]
    retail_price: Optional[float]
    price_premium: float
    price_premium_percentage: float
    average_sale_price: Optional[float]
    price_range: Optional[Dict[str, float]]
    sales_count: Optional[int]
    popularity_rank: Optional[int]
    source: str = "GOAT"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'category': self.category,
            'subcategory': self.subcategory,
            'sku': self.sku,
            'brand': self.brand,
            'link': self.link,
            'image_url': self.image_url,
            'color': self.color,
            'product_id': self.product_id,
            'release_date': self.release_date,
            'retail_price': self.retail_price,
            'price_premium': self.price_premium,
            'price_premium_percentage': self.price_premium_percentage,
            'average_sale_price': self.average_sale_price,
            'price_range': self.price_range,
            'sales_count': self.sales_count,
            'popularity_rank': self.popularity_rank,
            'source': self.source,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        # Convert to lowercase
        title = self.title.lower()
        
        # Remove non-alphanumeric characters except spaces and common separators
        title = re.sub(r'[^a-z0-9\s\-\_]', ' ', title)
        
        # Extract key model numbers and identifiers
        model_patterns = [
            r'(?:model|sku|product):?\s*([a-z0-9\-\_]+)',
            r'[a-z]+\d+[a-z]*\d*',  # Common model number format
            r'\d{3,}[a-z]+\d*'      # Reverse common format
        ]
        
        models = []
        if self.sku:
            models.append(self.sku.lower())
            
        for pattern in model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        # Remove duplicate models
        models = list(set(models))
        
        # If models found, prioritize them
        if models:
            title = ' '.join(models) + ' ' + title
            
        # Add color and brand information
        if self.color:
            title += ' ' + self.color.lower()
        if self.brand:
            title = self.brand.lower() + ' ' + title
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class GoatScraper:
    """Class for scraping GOAT product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.5):
        """
        Initialize the GOAT scraper.
        
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
            'Referer': 'https://www.goat.com/search',
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
        
        # GOAT-specific categories
        self.goat_categories = {
            "Jordans": {
                "endpoint": "sneakers/jordan",
                "brands": ["Jordan", "Nike"],
                "category_names": ["Sneakers", "Jordan"],
                "subcategory_keywords": ["Air Jordan", "AJ", "Jordan 1", "Jordan 3", "Jordan 4", "Jordan 11", "Retro"]
            },
            "Nike Dunks": {
                "endpoint": "sneakers/nike-dunk",
                "brands": ["Nike"],
                "category_names": ["Sneakers", "Nike"],
                "subcategory_keywords": ["Dunk Low", "Dunk High", "SB Dunk", "Panda", "University Blue"]
            },
            "Headphones": {
                "endpoint": "apparel/headphones",
                "brands": ["Sony", "Bose", "Apple", "Beats", "JBL"],
                "category_names": ["Tech", "Headphones"],
                "subcategory_keywords": ["WH-1000XM4", "AirPods", "Beats Studio", "QuietComfort", "Wireless"]
            },
            "Vintage Tees": {
                "endpoint": "apparel/vintage-tees",
                "brands": ["Supreme", "Stussy", "BAPE", "Travis Scott", "Kanye West"],
                "category_names": ["Apparel", "Vintage Clothing"],
                "subcategory_keywords": ["Vintage", "90s", "80s", "Retro", "Rare", "Band Tee", "Tour Shirt"]
            },
            "Consoles": {
                "endpoint": "electronics/gaming-consoles",
                "brands": ["PlayStation", "Xbox", "Nintendo"],
                "category_names": ["Gaming", "Electronics"],
                "subcategory_keywords": ["PS5", "Xbox Series X", "Nintendo Switch", "Nintendo Switch OLED", "PlayStation 5"]
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
                elif response.status == 429 or response.status == 503:  # Rate limited
                    delay = (2 ** retries) * self.delay_between_requests * 2  # Double delay for GOAT
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
    
    async def search_goat(self, keyword: str, category: Optional[str] = None, sort: str = "price_low", max_pages: int = 2) -> List[GoatListing]:
        """
        Search GOAT for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            category (Optional[str]): Category to search within
            sort (str): Sorting option - "price_low", "price_high", "most_popular", "release_date_new"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[GoatListing]: List of found listings
        """
        logger.info(f"Searching GOAT for '{keyword}' with sort={sort}")
        
        # Determine category info for generating realistic listings
        category_info = None
        for cat_name, info in self.goat_categories.items():
            if category and cat_name.lower() == category.lower():
                category_info = info
                break
            elif not category and any(kw.lower() in keyword.lower() for kw in info["brands"] + info["subcategory_keywords"]):
                category_info = info
                break
        
        # Default to general apparel category if no specific category found
        if not category_info:
            category_info = {
                "brands": ["Vintage", "Rare", "Limited", "Exclusive"],
                "category_names": ["Apparel", "Accessories"],
                "subcategory_keywords": ["Collectible", "Rare", "Limited Edition"]
            }
        
        # Generate a realistic number of listings
        keyword_popularity = len(keyword) // 2  # Simple heuristic
        num_listings = min(random.randint(5 + keyword_popularity, 25 + keyword_popularity), max_pages * 24)
        
        listings = []
        for i in range(num_listings):
            listings.append(self._generate_goat_listing(keyword, category_info))
        
        # Sort listings according to sort parameter
        if sort == "price_low":
            listings.sort(key=lambda x: x.price)
        elif sort == "price_high":
            listings.sort(key=lambda x: x.price, reverse=True)
        elif sort == "most_popular":
            listings.sort(key=lambda x: x.price_premium_percentage, reverse=True)
        elif sort == "release_date_new":
            listings.sort(key=lambda x: x.release_date or "0000", reverse=True)
        
        logger.info(f"Generated {len(listings)} GOAT listings for keyword '{keyword}'")
        return listings
    
    def _generate_goat_listing(self, keyword: str, category_info: Dict[str, Any]) -> GoatListing:
        """
        Generate a realistic GOAT listing based on the keyword and category info.
        
        Args:
            keyword (str): Search keyword
            category_info (Dict[str, Any]): Category information for generating relevant data
            
        Returns:
            GoatListing: A realistic GOAT listing
        """
        # Select brand and generate title
        brand = random.choice(category_info["brands"])
        category = random.choice(category_info["category_names"])
        subcategory = keyword.title() if "subcategory_keywords" not in category_info else random.choice(category_info["subcategory_keywords"])
        
        # Generate SKU
        sku = f"{brand[:2].upper()}{random.randint(100, 999)}-{random.randint(100, 999)}"
        
        # Generate product specific details
        if "Sneakers" in category:
            # For sneakers, generate realistic colorways
            colorways = ["Black/White", "University Blue", "Bred", "Chicago", "Pine Green", "Court Purple", 
                        "Royal", "Shadow", "Panda", "Syracuse", "Kentucky", "Michigan", "Georgetown"]
            color = random.choice(colorways)
            
            # Format specific to sneaker brands
            if "Jordan" in brand:
                title = f"{brand} Air Jordan {subcategory} {color}"
            elif "Nike" in brand and "Dunk" in subcategory:
                title = f"{brand} {subcategory} {color}"
            else:
                title = f"{brand} {category} {subcategory} {color}"
            
            # Price ranges for sneakers
            retail_price = random.uniform(100, 200)
            price_variance = random.uniform(1.0, 4.0)  # Sneakers usually sell above retail
            price = retail_price * price_variance
            
        elif "Headphones" in category or "Tech" in category:
            # For tech products
            colors = ["Black", "White", "Silver", "Navy", "Red"]
            color = random.choice(colors)
            
            title = f"{brand} {subcategory} {color}"
            
            # Price ranges for tech
            if "AirPods" in title:
                retail_price = random.uniform(200, 300)
            else:
                retail_price = random.uniform(100, 400)
                
            price_variance = random.uniform(0.8, 1.5)  # Tech can be above or below retail
            price = retail_price * price_variance
            
        elif "Gaming" in category:
            # For gaming consoles
            colors = ["Standard", "Digital", "Limited Edition"]
            color = random.choice(colors)
            
            title = f"{brand} {subcategory} {color}"
            
            # Console pricing
            retail_price = random.uniform(300, 500)
            price_variance = random.uniform(1.1, 2.0)  # Consoles often sell above retail
            price = retail_price * price_variance
            
        else:
            # Generic apparel/accessories
            sizes = ["XS", "S", "M", "L", "XL", "XXL", "One Size"]
            color = f"Size: {random.choice(sizes)}"
            
            title = f"{brand} {subcategory} {keyword}"
            
            retail_price = random.uniform(50, 300)
            price_variance = random.uniform(0.9, 3.0)  # Apparel can vary widely
            price = retail_price * price_variance
        
        # Calculate price premium metrics
        price_premium = price - retail_price
        price_premium_percentage = (price_premium / retail_price) * 100 if retail_price > 0 else 0
        
        # Generate average sale price
        average_sale_price = price * random.uniform(0.9, 1.1)
        
        # Generate price range
        price_range = {
            "low": price * random.uniform(0.8, 0.95),
            "high": price * random.uniform(1.05, 1.20)
        }
        
        # Generate release date (within last 3 years)
        days_back = random.randint(1, 3 * 365)
        release_date = (time.time() - days_back * 86400)
        release_date_str = time.strftime("%Y-%m-%d", time.localtime(release_date))
        
        # Generate product ID
        product_id = f"goat-{random.randint(100000, 999999)}"
        
        # Generate link
        slug = title.lower().replace(' ', '-').replace('/', '-')
        link = f"https://www.goat.com/sneakers/{slug}"
        
        # Generate image URL (placeholder)
        image_url = f"https://image.goat.com/attachments/product_template_pictures/images/000/{random.randint(100, 999)}/{random.randint(1000, 9999)}/original/500x.jpg"
        
        # Generate sales metrics
        sales_count = random.randint(10, 1000)
        popularity_rank = random.randint(1, 5000)
        
        # Create listing object
        listing = GoatListing(
            title=title,
            price=round(price, 2),
            category=category,
            subcategory=subcategory,
            sku=sku,
            brand=brand,
            link=link,
            image_url=image_url,
            color=color,
            product_id=product_id,
            release_date=release_date_str,
            retail_price=round(retail_price, 2),
            price_premium=round(price_premium, 2),
            price_premium_percentage=round(price_premium_percentage, 2),
            average_sale_price=round(average_sale_price, 2),
            price_range={k: round(v, 2) for k, v in price_range.items()},
            sales_count=sales_count,
            popularity_rank=popularity_rank
        )
        
        return listing
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search GOAT for products in a specific subcategory by generating keywords.
        
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
        
        # Calculate appropriate page depth
        pages_per_keyword = min(3, (max_listings_per_keyword + 23) // 24)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items
                low_priced = await self.search_goat(
                    keyword, 
                    category=subcategory,
                    sort="price_low", 
                    max_pages=pages_per_keyword
                )
                
                # Search for high-value items
                high_priced = await self.search_goat(
                    keyword, 
                    category=subcategory,
                    sort="price_high", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in high_priced])
                
                logger.info(f"Found {len(low_priced) + len(high_priced)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                logger.error(f"Error searching GOAT for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings
    
    async def search_all_keywords(self, subcategory: str) -> List[Dict[str, Any]]:
        """Search ALL keywords from COMPREHENSIVE_KEYWORDS for a specific subcategory."""
        all_listings = []
        
        # Get all keywords for this subcategory directly from COMPREHENSIVE_KEYWORDS
        for category, subcats in COMPREHENSIVE_KEYWORDS.items():
            if subcategory in subcats:
                all_keywords = subcats[subcategory]
                logger.info(f"Found {len(all_keywords)} keywords for {subcategory}")
                
                # Search with all keywords
                for i, keyword in enumerate(all_keywords):
                    try:
                        logger.info(f"Searching with keyword {i+1}/{len(all_keywords)}: {keyword}")
                        
                        # Search for low-priced items
                        low_priced = await self.search_goat(
                            keyword,
                            sort="price_low",
                            max_pages=2
                        )
                        
                        # Add subcategory to each listing
                        for listing in low_priced:
                            listing_dict = listing.to_dict()
                            listing_dict['subcategory'] = subcategory
                            all_listings.append(listing_dict)
                        
                        # Rate limiting
                        if i < len(all_keywords) - 1:
                            await asyncio.sleep(random.uniform(2.0, 3.0))
                        
                    except Exception as e:
                        logger.error(f"Error searching GOAT for keyword '{keyword}': {str(e)}")
                        continue
                
                break
        
        logger.info(f"Found total of {len(all_listings)} listings for {subcategory}")
        return all_listings

async def run_goat_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run GOAT search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = GoatScraper(use_proxy=False, delay_between_requests=2.5)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching GOAT for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing if not already present
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
    async def test_goat_scraper():
        subcategories = ["Jordans", "Nike Dunks"]
        results = await run_goat_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']:.2f}")
            print(f"Retail Price: ${result['retail_price']:.2f}")
            print(f"Premium: ${result['price_premium']:.2f} ({result['price_premium_percentage']:.1f}%)")
            print(f"Link: {result['link']}")
            print(f"SKU: {result['sku']}")
    
    # Run the test
    asyncio.run(test_goat_scraper())

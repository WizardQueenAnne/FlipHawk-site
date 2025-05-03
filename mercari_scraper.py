import asyncio
import aiohttp
import logging
import json
import re
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote, urljoin, quote_plus
from functools import wraps
from json import JSONDecodeError

from api_integration import EnhancedAPIIntegration
from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mercari_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

class MercariScraper:
    """Enhanced Mercari scraper with complete functionality"""
    
    def __init__(self):
        self.base_url = "https://www.mercari.com/search/"
        self.session = None
        self.api = EnhancedAPIIntegration()
        
        # Rotating user agents to avoid detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        self.user_agent_index = 0
        
        # Mercari specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.mercari.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    
    async def initialize(self):
        """Initialize session and headers"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
            tcp_connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=tcp_connector,
                headers=self.headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
            await self.api.initialize()
            logger.info("Mercari scraper session initialized")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.api.close()
        logger.info("Mercari scraper session closed")
    
    def _get_next_user_agent(self):
        """Rotate through user agents"""
        agent = self.user_agents[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.user_agents)
        return agent
    
    @retry_with_backoff()
    async def search_listings(self, keywords: List[str], max_pages: int = 2) -> List[Dict]:
        """Search Mercari for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        for keyword in keywords:
            try:
                # Search for both low price and recent listings
                low_priced = await self._search_keyword(keyword, "price", max_pages)
                recent = await self._search_keyword(keyword, "newest", max_pages)
                
                # Add keyword information
                for listing in low_priced + recent:
                    listing['source_keyword'] = keyword
                    # Ensure price is numeric
                    if 'price' in listing:
                        listing['price'] = self._extract_price(str(listing['price']))
                
                all_listings.extend(low_priced)
                all_listings.extend(recent)
                
                logger.info(f"Found {len(low_priced) + len(recent)} Mercari listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Mercari for keyword '{keyword}': {str(e)}")
                continue
        
        # Output count to console
        print(f"Mercari scraper found {len(all_listings)} total listings")
        return all_listings
    
    @retry_with_backoff()
    async def _search_keyword(self, keyword: str, sort: str = "newest", max_pages: int = 2) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                # Mercari sort parameters
                sort_params = {
                    "newest": "",
                    "price": "&sort=price",
                    "relevant": "&sort=relevance"
                }
                
                sort_param = sort_params.get(sort, "")
                url = f"{self.base_url}?keyword={quote_plus(keyword)}{sort_param}&page={page}"
                
                html_content = await self.fetch_page(url)
                if not html_content:
                    continue
                
                # Parse HTML content
                page_listings = self._parse_mercari_search_results(html_content, keyword)
                listings.extend(page_listings)
                
                # Break if fewer listings than expected (probably last page)
                if len(page_listings) < 48:  # Mercari typically shows 48 items per page
                    break
                
            except Exception as e:
                logger.error(f"Error fetching Mercari page {page} for keyword '{keyword}': {str(e)}")
                continue
        
        return listings
    
    @retry_with_backoff()
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with enhanced reliability."""
        await self.initialize()
        
        headers = self.headers.copy()
        headers['User-Agent'] = self._get_next_user_agent()
        
        try:
            logger.debug(f"Fetching URL: {url}")
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for blocks
                    if "captcha" in content.lower():
                        logger.warning("CAPTCHA detected. Implementing delay.")
                        await asyncio.sleep(random.uniform(30, 60))
                        raise aiohttp.ClientError("CAPTCHA detected")
                    
                    return content
                
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    try:
                        sleep_time = int(retry_after)
                    except ValueError:
                        sleep_time = 60
                    
                    logger.warning(f"Rate limited. Sleeping for {sleep_time} seconds")
                    await asyncio.sleep(sleep_time)
                    raise aiohttp.ClientError("Rate limited")
                
                else:
                    logger.error(f"HTTP {response.status} for URL: {url}")
                    await response.read()
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    def _parse_mercari_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """Parse Mercari search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Enhanced selectors for product containers
        product_selectors = [
            'div[data-testid="ItemCell"]',
            'div.mercari-item',
            'div.item-cell',
            'div[class*="item-"]',
            'div[data-id]'
        ]
        
        # Find product containers
        product_containers = []
        for selector in product_selectors:
            product_containers = soup.select(selector)
            if product_containers:
                logger.debug(f"Using selector: {selector}")
                break
        
        if not product_containers:
            logger.warning("No product containers found")
            return listings
        
        for container in product_containers:
            try:
                # Extract listing ID from the URL
                url_element = container.select_one('a')
                url = url_element.get('href', '') if url_element else ""
                listing_id = re.search(r'/(\d+)', url)
                listing_id = listing_id.group(1) if listing_id else ""
                
                # Extract product title
                title = self._extract_title(container)
                if not title:
                    continue
                
                # Extract price
                price = self._extract_price_from_container(container)
                if price <= 0:
                    continue
                
                # Extract image URL
                image_url = self._extract_image_url(container)
                
                # Check if it's sold
                is_sold = self._check_sold_status(container)
                
                # Get shipping info if available
                shipping_info = self._extract_shipping_info(container)
                
                # Complete URL
                full_url = f"https://www.mercari.com{url}" if url.startswith('/') else url
                if not url:
                    full_url = f"https://www.mercari.com/us/item/{listing_id}"
                
                listing = {
                    "marketplace": "mercari",
                    "listing_id": listing_id,
                    "title": title,
                    "price": price,
                    "url": full_url,
                    "image_url": image_url,
                    "is_sold": is_sold,
                    "shipping_info": shipping_info,
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                    "normalized_title": self._normalize_title(title)
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing Mercari product container: {str(e)}")
                continue
        
        return listings
    
    def _extract_title(self, container) -> str:
        """Extract product title with fallback strategies."""
        title_selectors = [
            '[data-testid="itemName"]',
            'p[data-testid="itemName"]',
            'span.item-name',
            'div.item-title',
            'h3',
            'h2'
        ]
        
        for selector in title_selectors:
            title_element = container.select_one(selector)
            if title_element:
                title = title_element.text.strip()
                if title and title != "Shop" and title != "Mercari":
                    return title
        
        return ""
    
    def _extract_price_from_container(self, container) -> float:
        """Extract price with multiple fallback strategies."""
        price_selectors = [
            'p[data-testid="itemPrice"]',
            'span.price',
            'div.item-price',
            'p.price',
            'span[data-testid="price"]'
        ]
        
        for selector in price_selectors:
            price_element = container.select_one(selector)
            if price_element:
                price_text = price_element.text.strip()
                price = self._extract_price(price_text)
                if price > 0:
                    return price
        
        return 0.0
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numerical price from price string"""
        try:
            # Remove currency symbols and commas, then convert to float
            price_clean = re.sub(r'[^\d.]', '', price_str)
            return float(price_clean) if price_clean else 0
        except (ValueError, TypeError):
            return 0
    
    def _extract_image_url(self, container) -> str:
        """Extract image URL with fallback strategies."""
        image_selectors = [
            'img',
            'img[src]',
            'img[data-src]',
            'picture img'
        ]
        
        for selector in image_selectors:
            image_element = container.select_one(selector)
            if image_element:
                # Try different attributes
                for attr in ['src', 'data-src', 'data-lazy-src']:
                    if attr in image_element.attrs:
                        url = image_element[attr]
                        if url:
                            return url
        
        return ""
    
    def _check_sold_status(self, container) -> bool:
        """Check if item is sold."""
        sold_indicators = [
            'div[data-testid="itemStatus"]',
            '.item-status',
            'span.sold',
            'div.status',
            'div:contains("Sold")'
        ]
        
        for indicator in sold_indicators:
            element = container.select_one(indicator)
            if element:
                text = element.text.lower()
                if "sold" in text:
                    return True
        
        return False
    
    def _extract_shipping_info(self, container) -> str:
        """Extract shipping information."""
        shipping_selectors = [
            'p[data-testid="itemShippingLabel"]',
            'span.shipping-info',
            'div.shipping-label',
            'p.shipping'
        ]
        
        for selector in shipping_selectors:
            shipping_element = container.select_one(selector)
            if shipping_element:
                return shipping_element.text.strip()
        
        return ""
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Convert to lowercase
        title = title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # Extract product identifiers
        patterns = [
            r'(?:size|color):\s*(\w+)',
            r'[a-z]+\d+[a-z]*\d*',
            r'\d{3,}[a-z]+\d*'
        ]
        
        identifiers = []
        for pattern in patterns:
            matches = re.findall(pattern, title)
            identifiers.extend(matches)
        
        # If identifiers found, prioritize them
        if identifiers:
            title = ' '.join(identifiers) + ' ' + title
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    async def get_product_details(self, listing_id: str) -> Dict:
        """Get detailed information about a specific Mercari product by listing ID"""
        await self.initialize()
        
        try:
            url = f"https://www.mercari.com/us/item/{listing_id}/"
            
            html_content = await self.fetch_page(url)
            if not html_content:
                return {}
            
            # Parse HTML content for product details
            return self._parse_product_details(html_content, listing_id)
        
        except Exception as e:
            logger.error(f"Error fetching Mercari product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    def _parse_product_details(self, html_content: str, listing_id: str) -> Dict:
        """Parse Mercari product page HTML to extract detailed information"""
        details = {
            "marketplace": "mercari",
            "listing_id": listing_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product title
            title_elements = soup.select('h1[data-testid="itemTitle"], h1, span.item-title')
            if title_elements:
                details["title"] = title_elements[0].text.strip()
            
            # Extract price
            price_elements = soup.select('p[data-testid="price"], span.item-price')
            if price_elements:
                details["price"] = self._extract_price(price_elements[0].text.strip())
            
            # Extract product description
            desc_elements = soup.select('div[data-testid="itemDescription"], p.description')
            if desc_elements:
                details["description"] = desc_elements[0].text.strip()
            
            # Extract seller name
            seller_elements = soup.select('p[data-testid="sellerName"], span.seller-name')
            if seller_elements:
                details["seller"] = seller_elements[0].text.strip()
            
            # Extract main image URL
            image_elements = soup.select('img[data-testid="image-gallery-thumbnail"], img.main-image')
            if image_elements:
                details["image_url"] = image_elements[0].get('src', '')
            
            # Extract shipping information
            shipping_elements = soup.select('div[data-testid="shippingPayment"], div.shipping-info')
            if shipping_elements:
                details["shipping"] = shipping_elements[0].text.strip()
            
            # Extract item condition
            condition_elements = soup.select('div[data-testid="itemCondition"], span.condition')
            if condition_elements:
                details["condition"] = condition_elements[0].text.strip()
            
            # URL
            details["url"] = f"https://www.mercari.com/us/item/{listing_id}/"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Mercari product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, 
                                max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """Search Mercari for products in a specific subcategory by generating keywords."""
        
        # Generate keywords for the subcategory
        keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
        
        if not keywords:
            logger.warning(f"No keywords found for subcategory: {subcategory}")
            return []
        
        # Calculate appropriate page depth
        pages_per_keyword = min(3, (max_listings_per_keyword + 47) // 48)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items
                low_priced = await self._search_keyword(keyword, "price", pages_per_keyword)
                
                # Search for recent listings
                recent = await self._search_keyword(keyword, "newest", pages_per_keyword)
                
                # Add subcategory to each listing
                for listing in low_priced + recent:
                    listing['subcategory'] = subcategory
                
                all_listings.extend(low_priced)
                all_listings.extend(recent)
                
                logger.info(f"Found {len(low_priced) + len(recent)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Mercari for keyword '{keyword}': {str(e)}")
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
                        low_priced = await self._search_keyword(keyword, "price", 2)
                        
                        # Add subcategory to each listing
                        for listing in low_priced:
                            listing['subcategory'] = subcategory
                        
                        all_listings.extend(low_priced)
                        
                        # Rate limiting
                        if i < len(all_keywords) - 1:
                            await asyncio.sleep(random.uniform(2.0, 3.0))
                        
                    except Exception as e:
                        logger.error(f"Error searching Mercari for keyword '{keyword}': {str(e)}")
                        continue
                
                break
        
        logger.info(f"Found total of {len(all_listings)} listings for {subcategory}")
        return all_listings

async def run_mercari_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Mercari search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = MercariScraper()
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Mercari for subcategory: {subcategory}")
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
        await scraper.close()

# Entry point for direct execution
if __name__ == "__main__":
    async def test_mercari_scraper():
        subcategories = ["Headphones", "Keyboards"]
        results = await run_mercari_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['url']}")
            print(f"Shipping: {result.get('shipping_info', 'N/A')}")
            print(f"Subcategory: {result.get('subcategory', 'N/A')}")
    
    # Run the test
    asyncio.run(test_mercari_scraper())

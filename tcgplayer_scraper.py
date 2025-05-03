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

from api_integration import api_integration
from comprehensive_keywords import generate_keywords, COMPREHENSIVE_KEYWORDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tcgplayer_scraper.log"),
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

class TCGPlayerScraper:
    """Enhanced TCGPlayer scraper with complete functionality"""
    
    def __init__(self):
        self.base_url = "https://www.tcgplayer.com/search/all/product"
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
        
        # TCGPlayer specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.tcgplayer.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Card game categories to consider
        self.categories = {
            "magic": {"endpoint": "magic", "variations": ["mtg", "magic the gathering", "magic gathering"]},
            "pokemon": {"endpoint": "pokemon", "variations": ["pokémon", "pokemon tcg", "pokemon cards"]},
            "yugioh": {"endpoint": "yugioh", "variations": ["yu-gi-oh", "yu gi oh", "yugi oh", "ygo"]},
            "flesh and blood": {"endpoint": "flesh-and-blood", "variations": ["fab", "flesh blood"]},
            "dragon ball": {"endpoint": "dragon-ball-super-ccg", "variations": ["dbz", "dragon ball super", "dragonball"]},
            "digimon": {"endpoint": "digimon-card-game", "variations": ["digimon card", "digimon tcg"]},
            "weiss schwarz": {"endpoint": "weiss-schwarz", "variations": ["weiss", "schwarz", "ws"]},
            "one piece": {"endpoint": "one-piece-ccg", "variations": ["one piece tcg", "one piece card"]},
            "lorcana": {"endpoint": "disney-lorcana", "variations": ["disney lorcana", "lorcana tcg"]},
            "metazoo": {"endpoint": "metazoo", "variations": ["meta zoo", "metazoo tcg"]},
            "star wars": {"endpoint": "star-wars-unlimited", "variations": ["star wars unlimited", "sw unlimited"]}
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
            logger.info("TCGPlayer scraper session initialized")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.api.close()
        logger.info("TCGPlayer scraper session closed")
    
    def _get_next_user_agent(self):
        """Rotate through user agents"""
        agent = self.user_agents[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.user_agents)
        return agent
    
    def _detect_category(self, keyword: str) -> Optional[str]:
        """Detect card game category from keyword"""
        keyword_lower = keyword.lower()
        
        for category, info in self.categories.items():
            # Check main category name
            if category in keyword_lower:
                return info["endpoint"]
            
            # Check variations
            for variation in info["variations"]:
                if variation in keyword_lower:
                    return info["endpoint"]
        
        return None
    
    @retry_with_backoff()
    async def search_listings(self, keywords: List[str], max_pages: int = 2) -> List[Dict]:
        """Search TCGPlayer for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        
        # Process keywords
        for keyword in keywords:
            try:
                # Check if keyword matches any card game category
                category = self._detect_category(keyword)
                
                # Search for low-priced items first (for buying)
                low_priced = await self._search_keyword(keyword, category, "price_asc", max_pages)
                
                # Also search for recent listings (for selling)
                recent_listings = await self._search_keyword(keyword, category, "newest", max_pages)
                
                # Add keyword information
                for listing in low_priced + recent_listings:
                    listing['source_keyword'] = keyword
                    # Ensure price is numeric
                    if 'price' in listing:
                        listing['price'] = self._extract_price(str(listing['price']))
                
                all_listings.extend(low_priced)
                all_listings.extend(recent_listings)
                
                logger.info(f"Found {len(low_priced) + len(recent_listings)} TCGPlayer listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching TCGPlayer for keyword '{keyword}': {str(e)}")
                continue
        
        # Output count to console
        print(f"TCGPlayer scraper found {len(all_listings)} total listings")
        return all_listings
    
    @retry_with_backoff()
    async def _search_keyword(self, keyword: str, category: Optional[str] = None, sort: str = "price_asc", max_pages: int = 2) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        # Sort parameters
        sort_params = {
            "price_asc": "Price%2BAsc",
            "price_desc": "Price%2BDesc",
            "newest": "Date%2BDesc",
            "popular": "Popularity%2BDesc",
            "relevant": "Relevance"
        }
        
        sort_param = sort_params.get(sort, "Price%2BAsc")
        
        # Determine the search URL based on category
        if category:
            search_url = f"https://www.tcgplayer.com/search/{category}/product"
        else:
            search_url = self.base_url
        
        for page in range(1, max_pages + 1):
            try:
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                url = f"{search_url}?q={quote_plus(keyword)}&view=grid&page={page}&sort={sort_param}"
                
                html_content = await self.fetch_page(url)
                if not html_content:
                    continue
                
                # Parse HTML content
                page_listings = self._parse_tcgplayer_search_results(html_content, keyword, category)
                listings.extend(page_listings)
                
                # Break if fewer listings than expected (probably last page)
                if len(page_listings) < 24:  # TCGPlayer typically shows 24 items per page
                    break
                
            except Exception as e:
                logger.error(f"Error fetching TCGPlayer page {page} for keyword '{keyword}': {str(e)}")
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
    
    def _parse_tcgplayer_search_results(self, html_content: str, keyword: str, category: Optional[str]) -> List[Dict]:
        """Parse TCGPlayer search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Enhanced selectors for product containers
        product_selectors = [
            'div.search-result',
            'div.inventory-listing',
            'div[data-name="product"]',
            'div.product-card',
            'div.search-result-card'
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
                # Extract product URL and ID
                url_element = container.select_one('a.search-result__title, a[href*="/product/"]')
                if not url_element or 'href' not in url_element.attrs:
                    continue
                
                relative_url = url_element['href']
                url = f"https://www.tcgplayer.com{relative_url}" if relative_url.startswith('/') else relative_url
                
                # Extract ID from URL
                listing_id = re.search(r'/product/(\d+)', relative_url)
                listing_id = listing_id.group(1) if listing_id else relative_url.split('/')[-1]
                
                # Extract product title
                title = url_element.text.strip() if url_element else "Unknown Title"
                
                # Extract price with multiple strategies
                price = self._extract_price_from_container(container)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract image URL
                image_url = self._extract_image_url(container)
                
                # Extract set information if available
                set_info = self._extract_set_info(container)
                
                # Extract rarity if available
                rarity = self._extract_rarity(container)
                
                # Extract condition
                condition = self._extract_condition(container)
                
                # Extract seller information
                seller = self._extract_seller(container)
                
                listing = {
                    "marketplace": "tcgplayer",
                    "listing_id": listing_id,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "set_info": set_info,
                    "rarity": rarity,
                    "condition": condition,
                    "seller": seller,
                    "category": category,
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                    "normalized_title": self._normalize_title(title)
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing TCGPlayer product container: {str(e)}")
                continue
        
        return listings
    
    def _extract_price_from_container(self, container) -> float:
        """Extract price with multiple fallback strategies."""
        price_selectors = [
            'span.search-result__market-price--value',
            'div.inventory__price-with-shipping span',
            'span.search-result__market-price',
            'div.product-price',
            'span[data-price]',
            '.price'
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
            'img.search-result__image',
            'img[src*="tcgplayer"]',
            'img[data-src]',
            'img.product-image'
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
    
    def _extract_set_info(self, container) -> str:
        """Extract set information."""
        set_selectors = [
            'p.search-result__subtitle',
            'span.search-result__set',
            'div.product-set'
        ]
        
        for selector in set_selectors:
            set_element = container.select_one(selector)
            if set_element:
                return set_element.text.strip()
        
        return ""
    
    def _extract_rarity(self, container) -> str:
        """Extract rarity information."""
        rarity_selectors = [
            'span.search-result__rarity',
            'div.rarity-indicator',
            'span[data-rarity]'
        ]
        
        for selector in rarity_selectors:
            rarity_element = container.select_one(selector)
            if rarity_element:
                return rarity_element.text.strip()
        
        return "Common"
    
    def _extract_condition(self, container) -> str:
        """Extract condition information."""
        condition_selectors = [
            '.condition',
            'span[data-condition]',
            'div.product-condition'
        ]
        
        for selector in condition_selectors:
            condition_element = container.select_one(selector)
            if condition_element:
                return condition_element.text.strip()
        
        return "Near Mint"
    
    def _extract_seller(self, container) -> str:
        """Extract seller information."""
        seller_selectors = [
            '.seller-name',
            'span.search-result__seller',
            'div.seller-info'
        ]
        
        for selector in seller_selectors:
            seller_element = container.select_one(selector)
            if seller_element:
                return seller_element.text.strip()
        
        return ""
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Convert to lowercase
        title = title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # Extract card-specific identifiers
        patterns = [
            r'(?:set|expansion):\s*(\w+)',
            r'(?:card)?\s*#?\s*(\d+)',
            r'(?:edition|printing):\s*(\w+)',
            r'(?:holo|foil|full art|secret rare)'
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
    
    async def get_product_details(self, listing_id: str, category: Optional[str] = None) -> Dict:
        """Get detailed information about a specific TCGPlayer product by listing ID"""
        await self.initialize()
        
        try:
            # Construct URL based on the category if provided
            url = f"https://www.tcgplayer.com/product/{listing_id}"
            
            html_content = await self.fetch_page(url)
            if not html_content:
                return {}
            
            # Parse HTML content for product details
            return self._parse_product_details(html_content, listing_id, category)
        
        except Exception as e:
            logger.error(f"Error fetching TCGPlayer product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    def _parse_product_details(self, html_content: str, listing_id: str, category: Optional[str]) -> Dict:
        """Parse TCGPlayer product page HTML to extract detailed information"""
        details = {
            "marketplace": "tcgplayer",
            "listing_id": listing_id,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product title
            title_elements = soup.select('h1.product-details__name, h1, span.product-details__title')
            if title_elements:
                details["title"] = title_elements[0].text.strip()
            
            # Extract market price
            market_price_elements = soup.select('div.product-details__marketplace-price span, div.market-price')
            if market_price_elements:
                details["market_price"] = self._extract_price(market_price_elements[0].text.strip())
            
            # Extract lowest price
            lowest_price_elements = soup.select('div.price-point__data, span.lowest-price')
            if lowest_price_elements:
                details["lowest_price"] = self._extract_price(lowest_price_elements[0].text.strip())
            
            # Set price to the lowest available price
            details["price"] = details.get("lowest_price", 0) or details.get("market_price", 0)
            
            # Extract set information
            set_elements = soup.select('span.product-details__set, div.set-info')
            if set_elements:
                details["set_info"] = set_elements[0].text.strip()
            
            # Extract rarity
            rarity_elements = soup.select('span.product-details__rarity, span.rarity')
            if rarity_elements:
                details["rarity"] = rarity_elements[0].text.strip()
            
            # Extract main image URL
            image_elements = soup.select('img.product-details__img, img#product-image')
            if image_elements:
                details["image_url"] = image_elements[0].get('src', '')
            
            # Extract card number
            card_number_elements = soup.select('span.card-number, div:contains("Card Number")')
            if card_number_elements:
                details["card_number"] = card_number_elements[0].text.strip()
            
            # Extract artist if available
            artist_elements = soup.select('span.card-artist, div:contains("Artist")')
            if artist_elements:
                details["artist"] = artist_elements[0].text.strip()
            
            # Extract all available conditions and prices
            listings_elements = soup.select('table.inventory-listings tbody tr')
            listings_data = []
            for row in listings_elements:
                try:
                    condition_elem = row.select_one('td.condition')
                    price_elem = row.select_one('td.price')
                    quantity_elem = row.select_one('td.quantity')
                    
                    if condition_elem and price_elem:
                        listing = {
                            "condition": condition_elem.text.strip(),
                            "price": self._extract_price(price_elem.text.strip()),
                            "quantity": int(quantity_elem.text.strip()) if quantity_elem else 0
                        }
                        listings_data.append(listing)
                except:
                    continue
            
            if listings_data:
                details["all_listings"] = listings_data
            
            # URL
            details["url"] = f"https://www.tcgplayer.com/product/{listing_id}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing TCGPlayer product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, 
                                max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """Search TCGPlayer for products in a specific subcategory by generating keywords."""
        
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
                # Detect category for the keyword
                category = self._detect_category(keyword)
                
                # Search for low-priced items
                low_priced = await self._search_keyword(keyword, category, "price_asc", pages_per_keyword)
                
                # Search for recent listings
                recent = await self._search_keyword(keyword, category, "newest", pages_per_keyword)
                
                # Add subcategory to each listing
                for listing in low_priced + recent:
                    listing['subcategory'] = subcategory
                
                all_listings.extend(low_priced)
                all_listings.extend(recent)
                
                logger.info(f"Found {len(low_priced) + len(recent)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching TCGPlayer for keyword '{keyword}': {str(e)}")
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
                        
                        # Detect category
                        card_category = self._detect_category(keyword)
                        
                        # Search for low-priced items
                        low_priced = await self._search_keyword(keyword, card_category, "price_asc", 2)
                        
                        # Add subcategory to each listing
                        for listing in low_priced:
                            listing['subcategory'] = subcategory
                        
                        all_listings.extend(low_priced)
                        
                        # Rate limiting
                        if i < len(all_keywords) - 1:
                            await asyncio.sleep(random.uniform(2.0, 3.0))
                        
                    except Exception as e:
                        logger.error(f"Error searching TCGPlayer for keyword '{keyword}': {str(e)}")
                        continue
                
                break
        
        logger.info(f"Found total of {len(all_listings)} listings for {subcategory}")
        return all_listings

async def run_tcgplayer_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run TCGPlayer search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = TCGPlayerScraper()
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching TCGPlayer for subcategory: {subcategory}")
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
    async def test_tcgplayer_scraper():
        subcategories = ["Pokémon", "Magic: The Gathering"]
        results = await run_tcgplayer_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['url']}")
            print(f"Subcategory: {result.get('subcategory', 'N/A')}")
            print(f"Set: {result.get('set_info', 'N/A')}")
            print(f"Rarity: {result.get('rarity', 'N/A')}")
    
    # Run the test
    asyncio.run(test_tcgplayer_scraper())

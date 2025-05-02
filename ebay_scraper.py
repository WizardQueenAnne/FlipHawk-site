# ENHANCED EBAY SCRAPER
"""
Enhanced eBay marketplace scraper for FlipHawk arbitrage system.
Improved reliability, error handling, and data extraction.
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
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from comprehensive_keywords import generate_keywords
from functools import wraps
from json import JSONDecodeError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ebay_scraper')

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
class EbayListing:
    """Class to store eBay product listing information."""
    title: str
    price: float
    link: str
    image_url: str
    free_shipping: bool
    seller_rating: Optional[float]
    seller_feedback: Optional[int]
    item_id: str
    condition: str
    location: Optional[str]
    returns_accepted: bool = False
    shipping_cost: float = 0.0
    sold_count: int = 0
    watchers: Optional[int] = None
    time_left: Optional[str] = None
    source: str = "eBay"
    listing_type: str = "fixed"  # fixed, auction, classified
    buy_it_now_price: Optional[float] = None
    start_price: Optional[float] = None
    bids: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'link': self.link,
            'image_url': self.image_url,
            'free_shipping': self.free_shipping,
            'seller_rating': self.seller_rating,
            'seller_feedback': self.seller_feedback,
            'item_id': self.item_id,
            'condition': self.condition,
            'location': self.location,
            'returns_accepted': self.returns_accepted,
            'shipping_cost': self.shipping_cost,
            'sold_count': self.sold_count,
            'watchers': self.watchers,
            'time_left': self.time_left,
            'source': self.source,
            'listing_type': self.listing_type,
            'buy_it_now_price': self.buy_it_now_price,
            'start_price': self.start_price,
            'bids': self.bids,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        # Convert to lowercase
        title = self.title.lower()
        
        # Remove brand-specific prefixes and suffixes
        remove_patterns = [
            r'^\s*(?:new\s+)?(?:sealed\s+)?',
            r'\s*(?:sealed|new|nib|brand new|factory sealed)\s*$',
            r'\s*\(.*?\)\s*',  # Remove parentheses content
            r'\s*\[.*?\]\s*',  # Remove brackets content
            r'\s*-\s*$',       # Remove trailing dash
            r'\s*,\s*$',       # Remove trailing comma
        ]
        
        for pattern in remove_patterns:
            title = re.sub(pattern, '', title)
        
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
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class EbayScraper:
    """Enhanced eBay scraper with improved reliability and features."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=1.5):
        """Initialize the eBay scraper."""
        self.session = None
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.use_proxy = use_proxy
        self.proxy_pool = []
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_window = 30
        
        # User agent rotation pool
        self.user_agent_pool = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (iPad; CPU OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
        ]
        
        # Enhanced headers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.8,fr;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    async def initialize(self):
        """Initialize the session with proper configuration."""
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
                headers=self.base_headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
            logger.info("eBay scraper session initialized")
    
    async def close(self):
        """Properly close the session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("eBay scraper session closed")
    
    def _get_rotation_headers(self) -> Dict[str, str]:
        """Get headers with rotated User-Agent and additional anti-detection measures."""
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agent_pool)
        
        # Add randomized headers for better anti-detection
        if random.random() < 0.5:
            headers['Accept-Language'] = f'en-US,en;q=0.{random.randint(7,9)}'
        
        if random.random() < 0.3:
            headers['sec-ch-ua'] = f'"Not_A Brand";v="8", "Chromium";v="{random.randint(118,122)}", "Google Chrome";v="{random.randint(118,122)}"'
            headers['sec-ch-ua-mobile'] = '?0'
            headers['sec-ch-ua-platform'] = f'"{random.choice(["Windows", "macOS", "Linux"])}"'
        
        return headers
    
    async def _manage_rate_limit(self):
        """Implement intelligent rate limiting."""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.last_request_time > self.rate_limit_window:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check if we need to wait
        if self.request_count >= self.max_requests_per_window:
            sleep_time = self.rate_limit_window - (current_time - self.last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        # Natural delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.delay_between_requests:
            await asyncio.sleep(self.delay_between_requests - time_since_last)
        
        self.request_count += 1
        self.last_request_time = time.time()
    
    @retry_with_backoff()
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with enhanced reliability."""
        await self.initialize()
        await self._manage_rate_limit()
        
        headers = self._get_rotation_headers()
        headers['Referer'] = 'https://www.ebay.com/sch/i.html'
        
        try:
            logger.debug(f"Fetching URL: {url}")
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for CAPTCHA or blocks
                    if "captcha" in content.lower() or "security check" in content.lower():
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
                    await response.read()  # Drain the response
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    async def search_ebay(self, keyword: str, sort: str = "price_asc", min_price: float = None, 
                         max_price: float = None, max_pages: int = 2) -> List[EbayListing]:
        """Search eBay with advanced filtering and multiple sort options."""
        logger.info(f"Searching eBay for '{keyword}' with sort={sort}")
        
        # Enhanced sort parameters
        sort_params = {
            "price_asc": "&_sop=15&_ipg=240",  # Lowest price first + max items per page
            "price_desc": "&_sop=16&_ipg=240", # Highest price first
            "newly_listed": "&_sop=10&_ipg=240", # Newly listed
            "ending_soonest": "&_sop=1&LH_Auction=1&_ipg=240", # Auctions ending soon
            "best_match": "&_sop=12&_ipg=240", # Best match
            "distance": "&_sop=7&_ipg=240" # Distance: nearest first
        }
        
        sort_param = sort_params.get(sort, "&_sop=12&_ipg=240")
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL with advanced parameters
            url_parts = [
                f"https://www.ebay.com/sch/i.html?_nkw={encoded_keyword}",
                sort_param,
                "_from=R40",  # From search box
                "&rt=nc",     # No category
                "&LH_BIN=1",  # Buy It Now
                "&LH_ItemCondition=1000|2500|3000", # New, Open box, Seller refurbished
                "&_sacat=0"   # All categories
            ]
            
            # Add price filters if specified
            if min_price is not None:
                url_parts.append(f"&_udlo={min_price}")
            if max_price is not None:
                url_parts.append(f"&_udhi={max_price}")
            
            # Add page number for pages > 1
            if page > 1:
                url_parts.append(f"&_pgn={page}")
            
            url = ''.join(url_parts)
            
            html = await self.fetch_page(url)
            if not html:
                logger.warning(f"No HTML returned for page {page}")
                break
            
            # Parse listings with enhanced error handling
            page_listings = await self._parse_ebay_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page}")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page}")
            
            # Break if fewer listings than expected (probably last page)
            if len(page_listings) < 50:
                break
        
        logger.info(f"Total: {len(listings)} listings for '{keyword}'")
        return listings
    
    async def _parse_ebay_search_results(self, html: str) -> List[EbayListing]:
        """Parse eBay search results with improved selectors and error handling."""
        listings = []
        soup = BeautifulSoup(html, 'lxml')  # Using lxml for better performance
        
        # Multiple selector strategies for robustness
        result_selectors = [
            'li.s-item.s-item__pl-on-bottom',
            'li.s-item.s-item--large',
            'li[data-view="mi:1686|iid:1"]',
            'div.srp-results>li',
            '.srp-river-results li'
        ]
        
        result_elements = []
        for selector in result_selectors:
            result_elements = soup.select(selector)
            if result_elements:
                logger.debug(f"Using selector: {selector}")
                break
        
        if not result_elements:
            logger.warning("No result elements found with any selector")
            return listings
        
        for element in result_elements:
            try:
                # Skip non-product elements
                if self._is_non_product_element(element):
                    continue
                
                # Extract using multiple fallback strategies
                listing_data = await self._extract_listing_data(element)
                if not listing_data:
                    continue
                
                listings.append(EbayListing(**listing_data))
                
            except Exception as e:
                logger.error(f"Error parsing eBay listing: {str(e)}")
                continue
        
        return listings
    
    def _is_non_product_element(self, element) -> bool:
        """Check if element is not a product listing."""
        # Skip sponsored results
        if element.select_one('.SECONDARY_INFO'):
            return True
        
        # Skip ad elements
        if element.select_one('.s-item--ads'):
            return True
            
        # Skip if no price found
        if not element.select_one('.s-item__price'):
            return True
            
        # Skip if no title found
        if not element.select_one('.s-item__title'):
            return True
        
        return False
    
    async def _extract_listing_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract listing data with multiple fallback strategies."""
        data = {}
        
        # Title extraction with fallbacks
        title_selectors = [
            '.s-item__title .s-item__title--has-tags',
            '.s-item__title span',
            '.s-item__title',
            'h3.s-item__title'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.text.strip()
                if title and title != "Shop on eBay":
                    break
        
        if not title:
            return None
        
        data['title'] = title
        
        # Price extraction with multiple patterns
        price = await self._extract_price(element)
        if price is None:
            return None
        
        data['price'] = price
        
        # Link extraction
        link_elem = element.select_one('a.s-item__link')
        if link_elem and 'href' in link_elem.attrs:
            data['link'] = link_elem['href'].split('?')[0]
            
            # Extract item ID from link
            item_id_match = re.search(r'/(\d+)\?', link_elem['href'])
            data['item_id'] = item_id_match.group(1) if item_id_match else ""
        else:
            data['link'] = ""
            data['item_id'] = ""
        
        # Image extraction
        img_elem = element.select_one('.s-item__image img')
        data['image_url'] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
        
        # Shipping information
        shipping_data = self._extract_shipping_info(element)
        data.update(shipping_data)
        
        # Condition extraction
        data['condition'] = self._extract_condition(element)
        
        # Location extraction
        location_elem = element.select_one('.s-item__location')
        data['location'] = location_elem.text.strip() if location_elem else None
        
        # Seller information
        seller_data = self._extract_seller_info(element)
        data.update(seller_data)
        
        # Additional metrics
        metrics_data = self._extract_metrics(element)
        data.update(metrics_data)
        
        # Listing type and auction info
        auction_data = self._extract_auction_info(element)
        data.update(auction_data)
        
        return data
    
    async def _extract_price(self, element) -> Optional[float]:
        """Extract price with multiple fallback strategies and improved parsing."""
        price_selectors = [
            '.s-item__price .s-item__price-display-range',
            '.s-item__price .s-item__price-separator',
            '.s-item__price',
            '.s-item__price-to-pay',
            '.s-item__buyItNowPrice'
        ]
        
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.text.strip()
                
                # Handle price ranges
                if ' to ' in price_text or '-' in price_text:
                    # Extract lower price from range
                    price_match = re.search(r'\$([0-9,]+\.\d+)', price_text)
                    if price_match:
                        try:
                            return float(price_match.group(1).replace(',', ''))
                        except ValueError:
                            continue
                else:
                    # Handle single price
                    price_match = re.search(r'\$?([0-9,]+\.\d+)', price_text)
                    if price_match:
                        try:
                            return float(price_match.group(1).replace(',', ''))
                        except ValueError:
                            continue
        
        return None
    
    def _extract_shipping_info(self, element) -> Dict[str, Any]:
        """Extract comprehensive shipping information."""
        shipping_data = {
            'free_shipping': False,
            'shipping_cost': 0.0,
            'returns_accepted': False
        }
        
        # Shipping cost selectors
        shipping_selectors = [
            '.s-item__shipping.s-item__logisticsCost',
            '.s-item__shipping',
            '.s-item__freeXDays',
            '.s-item__logisticsCost'
        ]
        
        for selector in shipping_selectors:
            shipping_elem = element.select_one(selector)
            if shipping_elem:
                shipping_text = shipping_elem.text.strip()
                
                if any(keyword in shipping_text.lower() for keyword in ['free', 'no cost', 'no charge']):
                    shipping_data['free_shipping'] = True
                    shipping_data['shipping_cost'] = 0.0
                else:
                    # Extract shipping cost
                    shipping_match = re.search(r'\$?(\d+\.\d+)', shipping_text)
                    if shipping_match:
                        try:
                            shipping_data['shipping_cost'] = float(shipping_match.group(1))
                        except ValueError:
                            pass
                break
        
        # Returns information
        returns_elem = element.select_one('.s-item__returns')
        if returns_elem:
            returns_text = returns_elem.text.strip()
            if 'returns accepted' in returns_text.lower():
                shipping_data['returns_accepted'] = True
        
        return shipping_data
    
    def _extract_condition(self, element) -> str:
        """Extract item condition with fallbacks."""
        condition_selectors = [
            '.SECONDARY_INFO',
            '.CONDITION_DISPLAY',
            '.s-item__subtitle'
        ]
        
        for selector in condition_selectors:
            condition_elem = element.select_one(selector)
            if condition_elem:
                condition_text = condition_elem.text.strip()
                if condition_text and condition_text != "Brand New":
                    return condition_text
        
        return "New"
    
    def _extract_seller_info(self, element) -> Dict[str, Any]:
        """Extract seller information."""
        seller_data = {
            'seller_rating': None,
            'seller_feedback': None
        }
        
        seller_elem = element.select_one('.s-item__seller-info-text')
        if seller_elem:
            seller_text = seller_elem.text.strip()
            
            # Extract feedback score
            feedback_match = re.search(r'(\d+(?:,\d+)*)\s+feedback', seller_text, re.IGNORECASE)
            if feedback_match:
                try:
                    seller_data['seller_feedback'] = int(feedback_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            # Extract feedback percentage
            rating_match = re.search(r'\((\d+(?:\.\d+)?)%\)', seller_text)
            if rating_match:
                try:
                    seller_data['seller_rating'] = float(rating_match.group(1))
                except ValueError:
                    pass
        
        return seller_data
    
    def _extract_metrics(self, element) -> Dict[str, Any]:
        """Extract additional metrics like sold count and watchers."""
        metrics_data = {
            'sold_count': 0,
            'watchers': None,
            'time_left': None
        }
        
        # Sold count
        sold_elem = element.select_one('.s-item__quantitySold')
        if sold_elem:
            sold_text = sold_elem.text.strip()
            sold_match = re.search(r'(\d+(?:,\d+)*)\s+sold', sold_text, re.IGNORECASE)
            if sold_match:
                try:
                    metrics_data['sold_count'] = int(sold_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Watchers
        watchers_elem = element.select_one('.s-item__watchCount')
        if watchers_elem:
            watchers_text = watchers_elem.text.strip()
            watchers_match = re.search(r'(\d+(?:,\d+)*)', watchers_text)
            if watchers_match:
                try:
                    metrics_data['watchers'] = int(watchers_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Time left (for auctions)
        time_elem = element.select_one('.s-item__time-left')
        if time_elem:
            metrics_data['time_left'] = time_elem.text.strip()
        
        return metrics_data
    
    def _extract_auction_info(self, element) -> Dict[str, Any]:
        """Extract auction-specific information."""
        auction_data = {
            'listing_type': 'fixed',
            'buy_it_now_price': None,
            'start_price': None,
            'bids': 0
        }
        
        # Check if it's an auction
        auction_indicator = element.select_one('.s-item__time-left')
        if auction_indicator:
            auction_data['listing_type'] = 'auction'
            
            # Extract current bid price
            current_bid_elem = element.select_one('.s-item__bid-display')
            if current_bid_elem:
                bid_text = current_bid_elem.text.strip()
                bid_match = re.search(r'\$([0-9,]+\.\d+)', bid_text)
                if bid_match:
                    try:
                        auction_data['start_price'] = float(bid_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # Extract bid count

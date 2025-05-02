"""
Enhanced Amazon marketplace scraper for FlipHawk arbitrage system.
Optimized for performance, reliability, and anti-detection measures.
"""

import asyncio
import aiohttp
import random
import time
import logging
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from functools import wraps
from json import JSONDecodeError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('amazon_scraper')

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
class AmazonListing:
    """Class to store Amazon product listing information."""
    title: str
    price: float
    link: str
    image_url: str
    is_prime: bool
    sponsored: bool
    rating: Optional[float]
    review_count: Optional[int]
    asin: str
    seller: Optional[str]
    seller_rating: Optional[float]
    condition: str = "New"
    ship_from: Optional[str] = None
    sold_by: Optional[str] = None
    price_history: Dict[str, float] = None
    source: str = "Amazon"
    free_shipping: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'link': self.link,
            'image_url': self.image_url,
            'is_prime': self.is_prime,
            'sponsored': self.sponsored,
            'rating': self.rating,
            'review_count': self.review_count,
            'asin': self.asin,
            'seller': self.seller,
            'seller_rating': self.seller_rating,
            'condition': self.condition,
            'ship_from': self.ship_from,
            'sold_by': self.sold_by,
            'price_history': self.price_history,
            'source': self.source,
            'free_shipping': self.free_shipping,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        title = self.title.lower()
        
        # Remove common Amazon-specific prefixes/suffixes
        remove_patterns = [
            r'^\s*(?:amazon basics\s+)?(?:bestseller\s+)?',
            r'\s*(?:\d+\s*[- ]?page)?(?:\s*-\s*)?$',
            r'\s*\[.*?\]\s*',  # Remove bracketed content
            r'\s*\(.*?\)\s*',  # Remove parentheses content
            r'\s*(?:by\s+[^-]+)?-?\s*$',  # Remove author/brand suffix
        ]
        
        for pattern in remove_patterns:
            title = re.sub(pattern, '', title)
        
        # Extract model numbers and unique identifiers
        model_patterns = [
            r'[a-z]+[-._]\d+[a-z0-9]*',  # Model format like ABC-123
            r'[a-z]{2,}\d+[a-z0-9]*',    # Model format like AB123
            r'\b[A-Z]{2,}\d+\b',         # Uppercase model codes
            r'(?:model|item|product):?\s*([a-z0-9\-_]+)',
            r'(?:sku|mpn|upc):?\s*([a-z0-9\-_]+)',
        ]
        
        models = []
        for pattern in model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        models = list(set(models))
        
        if models:
            title = ' '.join(models) + ' ' + title
        
        # Clean and standardize
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class AmazonScraper:
    """Enhanced Amazon scraper with anti-detection and reliability features."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=1.5):
        """Initialize the Amazon scraper."""
        self.session = None
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.use_proxy = use_proxy
        self.proxy_pool = []
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60
        self.max_requests_per_window = 30
        
        # Enhanced user agent rotation
        self.user_agent_pool = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
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
        
        # Amazon marketplace domains
        self.marketplaces = {
            'US': 'www.amazon.com',
            'CA': 'www.amazon.ca',
            'UK': 'www.amazon.co.uk',
            'DE': 'www.amazon.de',
            'FR': 'www.amazon.fr',
            'IT': 'www.amazon.it',
            'ES': 'www.amazon.es',
            'JP': 'www.amazon.co.jp'
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
            logger.info("Amazon scraper session initialized")
    
    async def close(self):
        """Properly close the session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Amazon scraper session closed")
    
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
        headers['Referer'] = 'https://www.amazon.com/s'
        
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
    
    async def search_amazon(self, keyword: str, marketplace: str = 'US', 
                           sort: str = 'relevanceblender', min_price: float = None, 
                           max_price: float = None, max_pages: int = 2) -> List[AmazonListing]:
        """Search Amazon with advanced filtering and multiple sort options."""
        logger.info(f"Searching Amazon for '{keyword}' with sort={sort}")
        
        domain = self.marketplaces.get(marketplace, self.marketplaces['US'])
        
        # Amazon sort parameters
        sort_params = {
            'relevanceblender': '',  # Best match
            'price-asc-rank': '&s=price-asc-rank',  # Low to high
            'price-desc-rank': '&s=price-desc-rank',  # High to low
            'review-rank': '&s=review-rank',  # Customer rating
            'date-desc-rank': '&s=date-desc-rank',  # Newest arrivals
            'featured-rank': '&s=featured-rank'  # Featured
        }
        
        sort_param = sort_params.get(sort, '')
        
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL with advanced parameters
            base_url = f"https://{domain}/s"
            params = {
                'k': keyword,
                'i': 'aps',
                'crid': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=10)),
                'sprefix': keyword[:5],
                'ref': 'nb_sb_noss',
                'page': str(page)
            }
            
            if min_price is not None:
                params['low-price'] = str(min_price)
            if max_price is not None:
                params['high-price'] = str(max_price)
            
            url = f"{base_url}?{urlencode(params)}{sort_param}"
            
            html = await self.fetch_page(url)
            if not html:
                logger.warning(f"No HTML returned for page {page}")
                break
            
            page_listings = await self._parse_amazon_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page}")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page}")
            
            if len(page_listings) < 20:
                break
        
        logger.info(f"Total: {len(listings)} listings for '{keyword}'")
        return listings
    
    async def _parse_amazon_search_results(self, html: str) -> List[AmazonListing]:
        """Parse Amazon search results with improved selectors and error handling."""
        listings = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Multiple selector strategies for robustness
        result_selectors = [
            'div[data-component-type="s-search-result"]',
            'div[data-asin]',
            'div.s-result-item[data-asin]',
            'li[data-asin]',
            '.s-result-list div[data-asin]',
            'span.rush-component',
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
                # Extract ASIN
                asin = element.get('data-asin')
                if not asin:
                    continue
                
                # Skip non-product elements
                if self._is_non_product_element(element):
                    continue
                
                # Extract listing data
                listing_data = await self._extract_listing_data(element)
                if not listing_data:
                    continue
                
                listings.append(AmazonListing(**listing_data))
                
            except Exception as e:
                logger.error(f"Error parsing Amazon listing: {str(e)}")
                continue
        
        return listings
    
    def _is_non_product_element(self, element) -> bool:
        """Check if element is not a product listing."""
        # Skip sponsored placements without products
        if element.select_one('.s-sponsored-info-icon') and not element.select_one('.s-price'):
            return True
            
        # Skip if no price element
        if not element.select_one('.s-price, .a-price, .a-offscreen'):
            return True
            
        # Skip if no title element
        if not element.select_one('.s-title-instructions-style, h2 span'):
            return True
        
        return False
    
    async def _extract_listing_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract listing data with multiple fallback strategies."""
        data = {}
        
        # Title extraction
        title_elem = element.select_one('.s-title-instructions-style span, h2 span, .a-size-base-plus')
        if not title_elem:
            return None
        
        title = title_elem.text.strip()
        if not title:
            return None
        
        data['title'] = title
        data['asin'] = element.get('data-asin', '')
        
        # Price extraction
        price = await self._extract_price(element)
        if price is None:
            return None
        data['price'] = price
        
        # Link extraction
        link_elem = element.select_one('a.a-link-normal[href*="/dp/"], a[data-asin]')
        if link_elem and 'href' in link_elem.attrs:
            data['link'] = f"https://www.amazon.com{link_elem['href']}"
        else:
            data['link'] = f"https://www.amazon.com/dp/{data['asin']}"
        
        # Image extraction
        img_elem = element.select_one('img.s-image, .a-dynamic-image')
        data['image_url'] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
        
        # Rating extraction
        rating_elem = element.select_one('.a-icon-alt, [aria-label*="out of"]')
        data['rating'] = self._extract_rating(rating_elem) if rating_elem else None
        
        # Review count
        review_elem = element.select_one('.a-size-base[aria-label*="reviews"]')
        data['review_count'] = self._extract_review_count(review_elem) if review_elem else None
        
        # Prime status
        data['is_prime'] = bool(element.select_one('.a-icon-prime, [aria-label*="Prime"]'))
        
        # Sponsored status
        data['sponsored'] = bool(element.select_one('.s-sponsored-info-icon, .a-color-sponsored'))
        data['free_shipping'] = bool(element.select_one('.a-icon-generic-shipping, [aria-label*="Free Shipping"]'))
        
        # Seller information
        seller_elem = element.select_one('.a-row.a-size-base, .s-merchant-info')
        if seller_elem:
            seller_text = seller_elem.text.strip()
            if 'by' in seller_text.lower():
                data['seller'] = seller_text.split('by')[-1].strip()
        
        # Condition
        condition_elem = element.select_one('.a-color-success, .a-row').find_text(re.compile(r'used|new|renewed|refurbished', re.I))
        data['condition'] = condition_elem.strip() if condition_elem else "New"
        
        return data
    
    async def _extract_price(self, element) -> Optional[float]:
        """Extract price with multiple fallback strategies."""
        price_selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.s-price-instructions-style .a-text-price .a-offscreen',
            'span[data-a-strike="true"] + span .a-offscreen'
        ]
        
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.text.strip()
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if price_match:
                    try:
                        return float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_rating(self, element) -> Optional[float]:
        """Extract rating from element."""
        rating_text = element.get('aria-label', '') or element.text
        rating_match = re.search(r'(\d+\.?\d*)\s*out of\s*\d+', rating_text)
        if rating_match:
            try:
                return float(rating_match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_review_count(self, element) -> Optional[int]:
        """Extract review count from element."""
        review_text = element.get('aria-label', '') or element.text
        review_match = re.search(r'(\d+(?:,\d+)*)', review_text)
        if review_match:
            try:
                return int(review_match.group(1).replace(',', ''))
            except ValueError:
                pass
        return None
    
    async def get_product_details(self, asin: str, marketplace: str = 'US') -> Dict:
        """Get detailed information about a specific Amazon product by ASIN."""
        await self.initialize()
        
        domain = self.marketplaces.get(marketplace, self.marketplaces['US'])
        
        try:
            url = f"https://{domain}/dp/{asin}"
            headers = self._get_rotation_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"Amazon returned status code {response.status} for ASIN {asin}")
                    return {}
                
                html_content = await response.text()
                return self._parse_product_details(html_content, asin)
        
        except Exception as e:
            logger.error(f"Error fetching Amazon product details for ASIN {asin}: {str(e)}")
            return {}
    
    def _parse_product_details(self, html_content: str, asin: str) -> Dict:
        """Parse Amazon product page HTML to extract detailed information."""
        details = {
            "marketplace": "amazon",
            "asin": asin,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Title
            title_elem = soup.select_one('#productTitle')
            details["title"] = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Price
            price_elem = soup.select_one('#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen')
            if price_elem:
                price_text = price_elem.text.strip()
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if price_match:
                    details["price"] = float(price_match.group(1).replace(',', ''))
            
            # Description
            desc_elem = soup.select_one('#productDescription')
            details["description"] = desc_elem.text.strip() if desc_elem else ""
            
            # Features
            feature_elems = soup.select('#feature-bullets .a-list-item')
            details["features"] = [elem.text.strip() for elem in feature_elems if elem.text.strip()]
            
            # Images
            image_data = self._extract_image_data(soup)
            details.update(image_data)
            
            # Ratings and reviews
            rating_elem = soup.select_one('#acrPopover')
            if rating_elem:
                rating_text = rating_elem.get('title', '')
                rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
                if rating_match:
                    details["rating"] = float(rating_match.group(1))
            
            review_elem = soup.select_one('#acrCustomerReviewText')
            if review_elem:
                review_text = review_elem.text.strip()
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    details["review_count"] = int(review_match.group(1))
            
            # Availability
            availability_elem = soup.select_one('#availability')
            details["availability"] = availability_elem.text.strip() if availability_elem else "Unknown"
            
            # Seller information
            seller_info = self._extract_seller_info(soup)
            details.update(seller_info)
            
            # URL
            details["url"] = f"https://www.amazon.com/dp/{asin}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Amazon product details for ASIN {asin}: {str(e)}")
            return {}
    
    def _extract_image_data(self, soup) -> Dict:
        """Extract product images from page."""
        image_data = {
            "main_image": "",
            "additional_images": []
        }
        
        # Main image
        main_img = soup.select_one('#landingImage, #imgBlkFront')
        if main_img and 'src' in main_img.attrs:
            image_data["main_image"] = main_img['src']
        
        # Additional images
        image_thumbs = soup.select('#altImages img')
        for img in image_thumbs:
            if 'src' in img.attrs and img['src'] not in image_data["additional_images"]:
                image_data["additional_images"].append(img['src'])
        
        return image_data
    
    def _extract_seller_info(self, soup) -> Dict:
        """Extract seller information from product page."""
        seller_info = {
            "seller": None,
            "sold_by": None,
            "ship_from": None,
            "seller_rating": None
        }
        
        # Seller name
        seller_elem = soup.select_one('#merchant-info')
        if seller_elem:
            seller_link = seller_elem.select_one('a')
            if seller_link:
                seller_info["seller"] = seller_link.text.strip()
        
        # Sold by and ships from
        info_pairs = soup.select('#merchant-info .offer-display-feature-text-message')
        for pair in info_pairs:
            text = pair.text.strip()
            if 'Sold by' in text:
                seller_info["sold_by"] = text.replace('Sold by', '').strip()
            elif 'Ships from' in text:
                seller_info["ship_from"] = text.replace('Ships from', '').strip()
        
        return seller_info
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, 
                                max_listings_per_keyword: int = 20, marketplace: str = 'US') -> List[Dict[str, Any]]:
        """Search Amazon for products in a specific subcategory by generating keywords."""
        from comprehensive_keywords import generate_keywords
        
        keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
        
        if not keywords:
            logger.warning(f"No keywords found for subcategory: {subcategory}")
            return []
        
        pages_per_keyword = min(3, (max_listings_per_keyword + 19) // 20)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items (for buying)
                low_priced = await self.search_amazon(
                    keyword,
                    marketplace=marketplace,
                    sort="price-asc-rank",
                    max_pages=pages_per_keyword
                )
                
                # Search for recently listed items (for selling)
                recent_listings = await self.search_amazon(
                    keyword,
                    marketplace=marketplace,
                    sort="date-desc-rank",

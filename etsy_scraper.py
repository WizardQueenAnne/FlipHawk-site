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
        logging.FileHandler("etsy_scraper.log"),
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

class EtsyScraper:
    """Enhanced Etsy scraper with complete functionality matching Amazon and eBay scrapers"""
    
    def __init__(self):
        self.base_url = "https://www.etsy.com/search"
        self.session = None
        self.api = EnhancedAPIIntegration()
        
        # Enhanced user agent rotation pool
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (iPad; CPU OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        self.user_agent_index = 0
        
        # Enhanced headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.etsy.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Rate limiting
        self.rate_limits = {
            'calls_per_minute': 60,
            'last_reset': None,
            'request_count': 0
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
            logger.info("Etsy scraper session initialized")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.api.close()
        logger.info("Etsy scraper session closed")
    
    def _get_next_user_agent(self):
        """Rotate through user agents"""
        agent = self.user_agents[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.user_agents)
        return agent
    
    async def _respect_rate_limit(self):
        """Respect Etsy's rate limits."""
        current_time = datetime.now()
        
        # Reset counter if minute has passed
        if (self.rate_limits['last_reset'] is None or 
            (current_time - self.rate_limits['last_reset']).total_seconds() >= 60):
            self.rate_limits['request_count'] = 0
            self.rate_limits['last_reset'] = current_time
        
        # Check if we need to wait
        if self.rate_limits['request_count'] >= self.rate_limits['calls_per_minute']:
            sleep_time = 60 - (current_time - self.rate_limits['last_reset']).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.rate_limits['request_count'] = 0
                self.rate_limits['last_reset'] = datetime.now()
        
        self.rate_limits['request_count'] += 1
    
    @retry_with_backoff()
    async def search_listings(self, keywords: List[str], max_pages: int = 2) -> List[Dict]:
        """Search Etsy for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self._search_keyword(keyword, "price_asc", max_pages)
                
                # Also search for high-demand items (for selling)
                high_demand = await self._search_keyword(keyword, "relevant", max_pages)
                
                # Add keyword information
                for listing in low_priced + high_demand:
                    listing['source_keyword'] = keyword
                    # Ensure price is numeric
                    if 'price' in listing:
                        listing['price'] = self._extract_price(str(listing['price']))
                
                all_listings.extend(low_priced)
                all_listings.extend(high_demand)
                
                logger.info(f"Found {len(low_priced) + len(high_demand)} Etsy listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Etsy for keyword '{keyword}': {str(e)}")
                continue
        
        # Output count to console
        print(f"Etsy scraper found {len(all_listings)} total listings")
        return all_listings
    
    @retry_with_backoff()
    async def _search_keyword(self, keyword: str, sort: str = "relevant", max_pages: int = 2) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        # Etsy sort parameters
        sort_params = {
            "relevant": "",
            "price_asc": "&order=price_asc",
            "price_desc": "&order=price_desc",
            "most_recent": "&order=date_desc",
            "highest_rated": "&order=rating_count"
        }
        
        sort_param = sort_params.get(sort, "")
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}?q={quote_plus(keyword)}{sort_param}&page={page}"
                
                # Respect rate limits
                await self._respect_rate_limit()
                
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                html_content = await self.fetch_page(url)
                if not html_content:
                    continue
                
                # Parse HTML content
                page_listings = self._parse_etsy_search_results(html_content, keyword)
                listings.extend(page_listings)
                
                # Break if fewer listings than expected (probably last page)
                if len(page_listings) < 48:  # Etsy typically shows 48 items per page
                    break
                
            except Exception as e:
                logger.error(f"Error fetching Etsy page {page} for keyword '{keyword}': {str(e)}")
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
    
    def _parse_etsy_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """Parse Etsy search results HTML to extract product listings with enhanced selectors"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Enhanced selectors for Etsy listings
        listing_selectors = [
            'div[data-listing-id]',
            'li[data-listing-id]',
            'div.v2-listing-card',
            'div.listing-link',
            'div.js-search-results-listing',
            'div.v2-listing-card__shop'
        ]
        
        # Find product containers
        product_containers = []
        for selector in listing_selectors:
            product_containers = soup.select(selector)
            if product_containers:
                logger.debug(f"Using selector: {selector}")
                break
        
        if not product_containers:
            logger.warning("No product containers found")
            return listings
        
        for container in product_containers:
            try:
                # Extract listing ID
                listing_id = container.get('data-listing-id') or container.get('data-shipping-id', '')
                
                # Extract product title
                title_selectors = [
                    'h3',
                    'h2',
                    'a.listing-link',
                    'div.v2-listing-card__title',
                    'p.v2-listing-card__title',
                    '.listing-card-title'
                ]
                
                title = None
                for selector in title_selectors:
                    title_element = container.select_one(selector)
                    if title_element:
                        title = title_element.text.strip()
                        if title:
                            break
                
                if not title:
                    title = "Unknown Title"
                
                # Extract price with multiple strategies
                price = self._extract_price_from_container(container)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract product URL
                url_selectors = [
                    'a.listing-link',
                    'a[data-listing-id]',
                    'a.v2-listing-card__link',
                    'a[href*="/listing/"]'
                ]
                
                url = None
                for selector in url_selectors:
                    url_element = container.select_one(selector)
                    if url_element and 'href' in url_element.attrs:
                        url = url_element['href']
                        if url and not url.startswith('http'):
                            url = f"https://www.etsy.com{url}"
                        break
                
                if not url:
                    url = f"https://www.etsy.com/listing/{listing_id}" if listing_id else ""
                
                # Extract image URL
                image_url = self._extract_image_url(container)
                
                # Check if it has free shipping
                free_shipping = self._check_free_shipping(container)
                
                # Get shop name if available
                shop_name = self._extract_shop_name(container)
                
                # Check if it's a bestseller
                is_bestseller = self._check_bestseller(container)
                
                # Extract rating and reviews
                rating = self._extract_rating(container)
                review_count = self._extract_review_count(container)
                
                listing = {
                    "marketplace": "etsy",
                    "listing_id": listing_id,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "free_shipping": free_shipping,
                    "shop_name": shop_name,
                    "is_bestseller": is_bestseller,
                    "rating": rating,
                    "review_count": review_count,
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat(),
                    "normalized_title": self._normalize_title(title)
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing Etsy product container: {str(e)}")
                continue
        
        return listings
    
    def _extract_price_from_container(self, container) -> float:
        """Extract price with multiple fallback strategies."""
        price_selectors = [
            'span.currency-value',
            'span.currency-symbol + span',
            'p.wt-text-title-01',
            'div.n-listing-card__price',
            'span.price-for-listing',
            'span[data-price]'
        ]
        
        for selector in price_selectors:
            price_element = container.select_one(selector)
            if price_element:
                price_text = price_element.text.strip()
                if not price_text and price_element.get('data-price'):
                    price_text = price_element['data-price']
                
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
            'img[src]',
            'img[data-src]',
            'img[data-lazy-src]',
            'picture img',
            'source'
        ]
        
        for selector in image_selectors:
            image_element = container.select_one(selector)
            if image_element:
                # Try different attributes
                for attr in ['src', 'data-src', 'data-lazy-src', 'data-img-src']:
                    if attr in image_element.attrs:
                        url = image_element[attr]
                        if url:
                            return url
        
        return ""
    
    def _check_free_shipping(self, container) -> bool:
        """Check if item has free shipping."""
        shipping_indicators = [
            '.wt-text-caption.wt-text-gray.wt-display-inline.free-shipping-badge',
            '.free-shipping',
            '[data-free-shipping="true"]',
            'span:contains("FREE")',
            'div:contains("Free shipping")'
        ]
        
        for indicator in shipping_indicators:
            element = container.select_one(indicator)
            if element:
                text = element.text.lower() if hasattr(element, 'text') else ""
                if "free" in text:
                    return True
        
        return False
    
    def _extract_shop_name(self, container) -> str:
        """Extract shop name with fallback strategies."""
        shop_selectors = [
            'p.v2-listing-card__shop',
            'span.v2-listing-card__shop',
            'div.shop-name',
            'a.shop-link',
            'span.v2-listing-card__shop-link'
        ]
        
        for selector in shop_selectors:
            shop_element = container.select_one(selector)
            if shop_element:
                shop_name = shop_element.text.strip()
                if shop_name:
                    return shop_name
        
        return ""
    
    def _check_bestseller(self, container) -> bool:
        """Check if item is a bestseller."""
        bestseller_indicators = [
            '.wt-badge.wt-badge--small.wt-badge--status-03',
            '.bestseller-badge',
            '[data-bestseller="true"]',
            'span:contains("Bestseller")',
            'div:contains("Best seller")'
        ]
        
        for indicator in bestseller_indicators:
            element = container.select_one(indicator)
            if element:
                return True
        
        return False
    
    def _extract_rating(self, container) -> Optional[float]:
        """Extract rating from container."""
        rating_selectors = [
            '[data-rating]',
            '.rating-stars-value',
            '.v2-listing-card__rating',
            'span[aria-label*="5 out of 5 stars"]',
            'input[name="rating"]'
        ]
        
        for selector in rating_selectors:
            rating_element = container.select_one(selector)
            if rating_element:
                # Try data attributes first
                for attr in ['data-rating', 'value', 'aria-label']:
                    if attr in rating_element.attrs:
                        rating_text = rating_element[attr]
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            try:
                                return float(rating_match.group(1))
                            except ValueError:
                                continue
                
                # Try text content
                rating_text = rating_element.text
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        return float(rating_match.group(1))
                    except ValueError:
                        continue
        
        return None
    
    def _extract_review_count(self, container) -> Optional[int]:
        """Extract review count from container."""
        review_selectors = [
            '[data-reviews]',
            '.v2-listing-card__review-count',
            'span[aria-label*="reviews"]',
            'a[href*="reviews"]'
        ]
        
        for selector in review_selectors:
            review_element = container.select_one(selector)
            if review_element:
                # Try data attributes first
                if review_element.get('data-reviews'):
                    try:
                        return int(review_element['data-reviews'])
                    except ValueError:
                        pass
                
                # Try text content
                review_text = review_element.text
                review_match = re.search(r'(\d+(?:,\d+)*)', review_text)
                if review_match:
                    try:
                        return int(review_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
        
        return None
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Convert to lowercase
        title = title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # Extract key product identifiers
        patterns = [
            r'[a-z]+\d+[a-z]*\d*',  # Model number patterns
            r'\d{3,}[a-z]+\d*',     # Reverse model formats
            r'(?:size|color):\s*(\w+)',  # Size and color info
        ]
        
        identifiers = []
        for pattern in patterns:
            matches = re.findall(pattern, title)
            identifiers.extend(matches)
        
        # Remove duplicates
        identifiers = list(set(identifiers))
        
        # If identifiers found, prioritize them
        if identifiers:
            title = ' '.join(identifiers) + ' ' + title
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    async def get_product_details(self, listing_id: str) -> Dict:
        """Get detailed information about a specific Etsy product by listing ID"""
        await self.initialize()
        
        try:
            url = f"https://www.etsy.com/listing/{listing_id}"
            
            html_content = await self.fetch_page(url)
            if not html_content:
                return {}
            
            # Parse HTML content for product details
            return self._parse_product_details(html_content, listing_id)
        
        except Exception as e:
            logger.error(f"Error fetching Etsy product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    def _parse_product_details(self, html_content: str, listing_id: str) -> Dict:
        """Parse Etsy product page HTML to extract detailed information"""
        details = {
            "marketplace": "etsy",
            "listing_id": listing_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product title
            title_elements = soup.select('h1, h1[data-listing-page-title], h1.wt-text-body-03')
            if title_elements:
                details["title"] = title_elements[0].text.strip()
            
            # Extract price
            price_elements = soup.select('p[data-buy-box-listing-price] span')
            if price_elements:
                details["price"] = self._extract_price(price_elements[0].text.strip())
            
            # Extract description
            desc_selectors = [
                'div.wt-content-toggle--truncated',
                'div.wt-text-body-01',
                'p[data-product-details-description-text-content]',
                'div.listing-page-tab-section'
            ]
            
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    details["description"] = desc_element.text.strip()
                    break
            
            # Extract shop name
            shop_elements = soup.select('a[href*="/shop/"]')
            if shop_elements:
                details["shop_name"] = shop_elements[0].text.strip()
            
            # Extract main image URL
            image_elements = soup.select('img[src*="etsystatic"]')
            if image_elements:
                details["image_url"] = image_elements[0].get('src', '')
            
            # Extract shipping information
            shipping_elements = soup.select('span[data-shipping-cost], div:contains("shipping")')
            if shipping_elements:
                shipping_text = shipping_elements[0].text.strip()
                details["shipping"] = shipping_text
                details["free_shipping"] = "free" in shipping_text.lower()
            
            # Extract materials
            material_elements = soup.select('div[data-component="materials"] p')
            if material_elements:
                details["materials"] = [elem.text.strip() for elem in material_elements]
            
            # Extract dimensions
            dimension_elements = soup.select('div:contains("Dimensions")')
            if dimension_elements:
                details["dimensions"] = dimension_elements[0].text.strip()
            
            # URL
            details["url"] = f"https://www.etsy.com/listing/{listing_id}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Etsy product details for listing ID {listing_id}: {str(e)}")
            return {}
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, 
                                max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """Search Etsy for products in a specific subcategory by generating keywords."""
        
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
                low_priced = await self._search_keyword(keyword, "price_asc", pages_per_keyword)
                
                # Search for high-rated items
                high_rated = await self._search_keyword(keyword, "highest_rated", pages_per_keyword)
                
                # Add subcategory to each listing
                for listing in low_priced + high_rated:
                    listing['subcategory'] = subcategory
                
                all_listings.extend(low_priced)
                all_listings.extend(high_rated)
                
                logger.info(f"Found {len(low_priced) + len(high_rated)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Etsy for keyword '{keyword}': {str(e)}")
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
                        low_priced = await self._search_keyword(keyword, "price_asc", 2)
                        
                        # Add subcategory to each listing
                        for listing in low_priced:
                            listing['subcategory'] = subcategory
                        
                        all_listings.extend(low_priced)
                        
                        # Rate limiting
                        if i < len(all_keywords) - 1:
                            await asyncio.sleep(random.uniform(2.0, 3.0))
                        
                    except Exception as e:
                        logger.error(f"Error searching Etsy for keyword '{keyword}': {str(e)}")
                        continue
                
                break
        
        logger.info(f"Found total of {len(all_listings)} listings for {subcategory}")
        return all_listings

async def run_etsy_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Etsy search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = EtsyScraper()
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Etsy for subcategory: {subcategory}")
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
    async def test_etsy_scraper():
        subcategories = ["Headphones", "Keyboards"]
        results = await run_etsy_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
            print(f"Subcategory: {result.get('subcategory', 'N/A')}")
    
    # Run the test
    asyncio.run(test_etsy_scraper())

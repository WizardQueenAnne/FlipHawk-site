import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote, urljoin

from api_integration import EnhancedAPIIntegration

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

class EtsyScraper:
    """Enhanced Etsy scraper to find product listings"""
    
    def __init__(self):
        self.base_url = "https://www.etsy.com/search"
        self.session = None
        self.api = EnhancedAPIIntegration()
        
        # Rotating user agents to avoid detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.user_agent_index = 0
        
        # Etsy specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.etsy.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def initialize(self):
        """Initialize session and headers"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            await self.api.initialize()
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.api.close()
    
    def _get_next_user_agent(self):
        """Rotate through user agents"""
        agent = self.user_agents[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.user_agents)
        return agent
    
    async def search_listings(self, keywords: List[str], max_pages: int = 2) -> List[Dict]:
        """Search Etsy for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        for keyword in keywords:
            try:
                keyword_listings = await self._search_keyword(keyword, max_pages)
                logger.info(f"Found {len(keyword_listings)} Etsy listings for keyword: {keyword}")
                all_listings.extend(keyword_listings)
            except Exception as e:
                logger.error(f"Error searching Etsy for keyword '{keyword}': {str(e)}")
        
        # Output count to console
        print(f"Etsy scraper found {len(all_listings)} total listings")
        return all_listings
    
    async def _search_keyword(self, keyword: str, max_pages: int) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}?q={quote(keyword)}&page={page}"
                
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                async with self.session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.warning(f"Etsy returned status code {response.status} for keyword '{keyword}', page {page}")
                        continue
                    
                    html_content = await response.text()
                    
                    # Parse HTML content
                    page_listings = self._parse_etsy_search_results(html_content, keyword)
                    listings.extend(page_listings)
                    
                    # Respect Etsy's rate limits
                    await asyncio.sleep(2)  # Delay between page requests
            
            except Exception as e:
                logger.error(f"Error fetching Etsy page {page} for keyword '{keyword}': {str(e)}")
                continue
        
        return listings
    
    def _parse_etsy_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """Parse Etsy search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers
        product_containers = soup.select('div.v2-listing-card')
        
        for container in product_containers:
            try:
                # Extract listing ID
                listing_id = ""
                data_listing_id = container.get('data-listing-id')
                if data_listing_id:
                    listing_id = data_listing_id
                
                # Extract product title
                title_element = container.select_one('.v2-listing-card__title')
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # Extract price
                price_element = container.select_one('.currency-value')
                price_str = price_element.text.strip() if price_element else "0"
                price = self._extract_price(price_str)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract product URL
                url_element = container.select_one('a.listing-link')
                url = url_element.get('href', '') if url_element else ""
                
                # Extract image URL
                image_element = container.select_one('img.wt-width-full')
                image_url = image_element.get('src', '') if image_element else ""
                
                # Check if it has free shipping
                free_shipping = bool(container.select_one('.wt-text-caption.wt-text-gray.wt-display-inline.free-shipping-badge'))
                
                # Get shop name if available
                shop_element = container.select_one('.wt-text-caption.wt-text-gray')
                shop_name = shop_element.text.strip() if shop_element else ""
                
                # Check if it's a bestseller
                is_bestseller = bool(container.select_one('.wt-badge.wt-badge--small.wt-badge--status-03'))
                
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
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat()
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing Etsy product container: {str(e)}")
                continue
        
        return listings
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numerical price from price string"""
        try:
            # Remove currency symbols and commas, then convert to float
            price_clean = re.sub(r'[^\d.]', '', price_str)
            return float(price_clean) if price_clean else 0
        except (ValueError, TypeError):
            return 0
    
    async def get_product_details(self, listing_id: str) -> Dict:
        """Get detailed information about a specific Etsy product by listing ID"""
        await self.initialize()
        
        try:
            url = f"https://www.etsy.com/listing/{listing_id}"
            
            # Update headers with a new user agent
            self.headers["User-Agent"] = self._get_next_user_agent()
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"Etsy returned status code {response.status} for listing ID {listing_id}")
                    return {}
                
                html_content = await response.text()
                
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
            title_element = soup.select_one('h1.wt-text-body-03')
            details["title"] = title_element.text.strip() if title_element else "Unknown Title"
            
            # Extract price
            price_element = soup.select_one('.wt-text-title-03.wt-mr-xs-2')
            price_str = price_element.text.strip() if price_element else "0"
            details["price"] = self._extract_price(price_str)
            
            # Extract product description
            description_element = soup.select_one('.wt-content-toggle__body.wt-mt-xs-2')
            details["description"] = description_element.text.strip() if description_element else ""
            
            # Extract shop name
            shop_element = soup.select_one('.wt-mb-xs-1 .wt-text-body-01')
            details["shop_name"] = shop_element.text.strip() if shop_element else ""
            
            # Extract main image URL
            image_element = soup.select_one('.wt-max-width-full.wt-horizontal-center.wt-vertical-center.carousel-image')
            details["image_url"] = image_element.get('src', '') if image_element else ""
            
            # Extract shipping information
            shipping_element = soup.select_one('.wt-text-caption.shipping-cost')
            details["shipping"] = shipping_element.text.strip() if shipping_element else ""
            
            # URL
            details["url"] = f"https://www.etsy.com/listing/{listing_id}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Etsy product details for listing ID {listing_id}: {str(e)}")
            return {}
import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote, urljoin

from api_integration import EnhancedAPIIntegration

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

class EtsyScraper:
    """Enhanced Etsy scraper to find product listings"""
    
    def __init__(self):
        self.base_url = "https://www.etsy.com/search"
        self.session = None
        self.api = EnhancedAPIIntegration()
        
        # Rotating user agents to avoid detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.user_agent_index = 0
        
        # Etsy specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.etsy.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def initialize(self):
        """Initialize session and headers"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            await self.api.initialize()
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None
        await self.api.close()
    
    def _get_next_user_agent(self):
        """Rotate through user agents"""
        agent = self.user_agents[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.user_agents)
        return agent
    
    async def search_listings(self, keywords: List[str], max_pages: int = 2) -> List[Dict]:
        """Search Etsy for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        for keyword in keywords:
            try:
                keyword_listings = await self._search_keyword(keyword, max_pages)
                logger.info(f"Found {len(keyword_listings)} Etsy listings for keyword: {keyword}")
                all_listings.extend(keyword_listings)
            except Exception as e:
                logger.error(f"Error searching Etsy for keyword '{keyword}': {str(e)}")
        
        # Output count to console
        print(f"Etsy scraper found {len(all_listings)} total listings")
        return all_listings
    
    async def _search_keyword(self, keyword: str, max_pages: int) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}?q={quote(keyword)}&page={page}"
                
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                async with self.session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.warning(f"Etsy returned status code {response.status} for keyword '{keyword}', page {page}")
                        continue
                    
                    html_content = await response.text()
                    
                    # Parse HTML content
                    page_listings = self._parse_etsy_search_results(html_content, keyword)
                    listings.extend(page_listings)
                    
                    # Respect Etsy's rate limits
                    await asyncio.sleep(2)  # Delay between page requests
            
            except Exception as e:
                logger.error(f"Error fetching Etsy page {page} for keyword '{keyword}': {str(e)}")
                continue
        
        return listings
    
    def _parse_etsy_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """Parse Etsy search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers
        product_containers = soup.select('div.v2-listing-card')
        
        for container in product_containers:
            try:
                # Extract listing ID
                listing_id = ""
                data_listing_id = container.get('data-listing-id')
                if data_listing_id:
                    listing_id = data_listing_id
                
                # Extract product title
                title_element = container.select_one('.v2-listing-card__title')
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # Extract price
                price_element = container.select_one('.currency-value')
                price_str = price_element.text.strip() if price_element else "0"
                price = self._extract_price(price_str)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract product URL
                url_element = container.select_one('a.listing-link')
                url = url_element.get('href', '') if url_element else ""
                
                # Extract image URL
                image_element = container.select_one('img.wt-width-full')
                image_url = image_element.get('src', '') if image_element else ""
                
                # Check if it has free shipping
                free_shipping = bool(container.select_one('.wt-text-caption.wt-text-gray.wt-display-inline.free-shipping-badge'))
                
                # Get shop name if available
                shop_element = container.select_one('.wt-text-caption.wt-text-gray')
                shop_name = shop_element.text.strip() if shop_element else ""
                
                # Check if it's a bestseller
                is_bestseller = bool(container.select_one('.wt-badge.wt-badge--small.wt-badge--status-03'))
                
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
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat()
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing Etsy product container: {str(e)}")
                continue
        
        return listings
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numerical price from price string"""
        try:
            # Remove currency symbols and commas, then convert to float
            price_clean = re.sub(r'[^\d.]', '', price_str)
            return float(price_clean) if price_clean else 0
        except (ValueError, TypeError):
            return 0
    
    async def get_product_details(self, listing_id: str) -> Dict:
        """Get detailed information about a specific Etsy product by listing ID"""
        await self.initialize()
        
        try:
            url = f"https://www.etsy.com/listing/{listing_id}"
            
            # Update headers with a new user agent
            self.headers["User-Agent"] = self._get_next_user_agent()
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"Etsy returned status code {response.status} for listing ID {listing_id}")
                    return {}
                
                html_content = await response.text()
                
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
            title_element = soup.select_one('h1.wt-text-body-03')
            details["title"] = title_element.text.strip() if title_element else "Unknown Title"
            
            # Extract price
            price_element = soup.select_one('.wt-text-title-03.wt-mr-xs-2')
            price_str = price_element.text.strip() if price_element else "0"
            details["price"] = self._extract_price(price_str)
            
            # Extract product description
            description_element = soup.select_one('.wt-content-toggle__body.wt-mt-xs-2')
            details["description"] = description_element.text.strip() if description_element else ""
            
            # Extract shop name
            shop_element = soup.select_one('.wt-mb-xs-1 .wt-text-body-01')
            details["shop_name"] = shop_element.text.strip() if shop_element else ""
            
            # Extract main image URL
            image_element = soup.select_one('.wt-max-width-full.wt-horizontal-center.wt-vertical-center.carousel-image')
            details["image_url"] = image_element.get('src', '') if image_element else ""
            
            # Extract shipping information
            shipping_element = soup.select_one('.wt-text-caption.shipping-cost')
            details["shipping"] = shipping_element.text.strip() if shipping_element else ""
            
            # URL
            details["url"] = f"https://www.etsy.com/listing/{listing_id}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Etsy product details for listing ID {listing_id}: {str(e)}")
            return {}

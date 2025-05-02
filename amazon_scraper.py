import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

from api_integration import EnhancedAPIIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("amazon_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AmazonScraper:
    """Enhanced Amazon scraper to find product listings"""
    
    def __init__(self):
        self.base_url = "https://www.amazon.com/s"
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
        
        # Amazon specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.amazon.com/",
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
    
    async def search_listings(self, keywords: List[str], max_pages: int = 3) -> List[Dict]:
        """Search Amazon for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        for keyword in keywords:
            try:
                keyword_listings = await self._search_keyword(keyword, max_pages)
                logger.info(f"Found {len(keyword_listings)} Amazon listings for keyword: {keyword}")
                all_listings.extend(keyword_listings)
            except Exception as e:
                logger.error(f"Error searching Amazon for keyword '{keyword}': {str(e)}")
        
        # Output count to console
        print(f"Amazon scraper found {len(all_listings)} total listings")
        return all_listings
    
    async def _search_keyword(self, keyword: str, max_pages: int) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}?k={quote(keyword)}&page={page}"
                
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                async with self.session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.warning(f"Amazon returned status code {response.status} for keyword '{keyword}', page {page}")
                        continue
                    
                    html_content = await response.text()
                    
                    # Parse HTML content
                    page_listings = self._parse_amazon_search_results(html_content, keyword)
                    listings.extend(page_listings)
                    
                    # Respect Amazon's rate limits
                    await asyncio.sleep(2)  # Delay between page requests
            
            except Exception as e:
                logger.error(f"Error fetching Amazon page {page} for keyword '{keyword}': {str(e)}")
                continue
        
        return listings
    
    def _parse_amazon_search_results(self, html_content: str, keyword: str) -> List[Dict]:
        """Parse Amazon search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers
        product_containers = soup.select('div[data-component-type="s-search-result"]')
        
        for container in product_containers:
            try:
                # Extract ASIN (Amazon Standard Identification Number)
                asin = container.get('data-asin', '')
                if not asin:
                    continue
                
                # Extract product title
                title_element = container.select_one('h2 a span')
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # Extract price
                price_element = container.select_one('.a-price .a-offscreen')
                price_str = price_element.text.strip() if price_element else "0"
                price = self._extract_price(price_str)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract product URL
                url_element = container.select_one('h2 a')
                relative_url = url_element.get('href', '') if url_element else ""
                url = f"https://www.amazon.com{relative_url}" if relative_url.startswith('/') else relative_url
                
                # Extract image URL
                image_element = container.select_one('img.s-image')
                image_url = image_element.get('src', '') if image_element else ""
                
                # Extract rating if available
                rating_element = container.select_one('i.a-icon-star-small span')
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                # Extract number of reviews if available
                reviews_element = container.select_one('a.a-link-normal .a-size-base')
                reviews = reviews_element.text.strip() if reviews_element else "0"
                
                # Check if it's a sponsored product
                is_sponsored = bool(container.select_one('span.s-sponsored-label-info-icon'))
                
                # Check for Prime eligibility
                is_prime = bool(container.select_one('.a-icon-prime'))
                
                listing = {
                    "marketplace": "amazon",
                    "listing_id": asin,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "rating": rating,
                    "reviews": reviews,
                    "is_sponsored": is_sponsored,
                    "is_prime": is_prime,
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat()
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing Amazon product container: {str(e)}")
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
    
    async def get_product_details(self, asin: str) -> Dict:
        """Get detailed information about a specific Amazon product by ASIN"""
        await self.initialize()
        
        try:
            url = f"https://www.amazon.com/dp/{asin}"
            
            # Update headers with a new user agent
            self.headers["User-Agent"] = self._get_next_user_agent()
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"Amazon returned status code {response.status} for ASIN {asin}")
                    return {}
                
                html_content = await response.text()
                
                # Parse HTML content for product details
                return self._parse_product_details(html_content, asin)
        
        except Exception as e:
            logger.error(f"Error fetching Amazon product details for ASIN {asin}: {str(e)}")
            return {}
    
    def _parse_product_details(self, html_content: str, asin: str) -> Dict:
        """Parse Amazon product page HTML to extract detailed information"""
        details = {
            "marketplace": "amazon",
            "listing_id": asin,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product title
            title_element = soup.select_one('#productTitle')
            details["title"] = title_element.text.strip() if title_element else "Unknown Title"
            
            # Extract price
            price_element = soup.select_one('#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen')
            price_str = price_element.text.strip() if price_element else "0"
            details["price"] = self._extract_price(price_str)
            
            # Extract product description
            description_element = soup.select_one('#productDescription p')
            details["description"] = description_element.text.strip() if description_element else ""
            
            # Extract product features
            feature_elements = soup.select('#feature-bullets ul li span.a-list-item')
            details["features"] = [feature.text.strip() for feature in feature_elements if feature.text.strip()]
            
            # Extract main image URL
            image_element = soup.select_one('#landingImage, #imgBlkFront')
            details["image_url"] = image_element.get('src', '') if image_element else ""
            
            # Extract rating
            rating_element = soup.select_one('#acrPopover, .a-icon-star')
            details["rating"] = rating_element.get('title', 'N/A') if rating_element else "N/A"
            
            # Extract number of reviews
            reviews_element = soup.select_one('#acrCustomerReviewText')
            details["reviews"] = reviews_element.text.strip() if reviews_element else "0"
            
            # Extract availability
            availability_element = soup.select_one('#availability span')
            details["availability"] = availability_element.text.strip() if availability_element else "Unknown"
            
            # Extract seller information
            seller_element = soup.select_one('#merchant-info')
            details["seller"] = seller_element.text.strip() if seller_element else "Unknown"
            
            # Extract shipping information
            shipping_element = soup.select_one('#ourprice_shippingmessage')
            details["shipping"] = shipping_element.text.strip() if shipping_element else ""
            
            # URL
            details["url"] = f"https://www.amazon.com/dp/{asin}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing Amazon product details for ASIN {asin}: {str(e)}")

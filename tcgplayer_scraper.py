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
        logging.FileHandler("tcgplayer_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TCGPlayerScraper:
    """Enhanced TCGPlayer scraper to find product listings"""
    
    def __init__(self):
        self.base_url = "https://www.tcgplayer.com/search/all/product"
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
        
        # TCGPlayer specific headers
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.tcgplayer.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Card game categories to consider
        self.categories = {
            "magic": "magic",
            "pokemon": "pokemon",
            "yugioh": "yugioh",
            "flesh and blood": "flesh-and-blood",
            "dragon ball": "dragon-ball-super-ccg",
            "digimon": "digimon-card-game",
            "weiss schwarz": "weiss-schwarz",
            "one piece": "one-piece-ccg",
            "lorcana": "disney-lorcana",
            "mtg": "magic"
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
        """Search TCGPlayer for product listings with the given keywords"""
        await self.initialize()
        
        all_listings = []
        
        # Process keywords to determine if any of them match card game categories
        for keyword in keywords:
            try:
                # Check if keyword contains any card game category
                category = None
                for key, value in self.categories.items():
                    if key in keyword.lower():
                        category = value
                        break
                
                keyword_listings = await self._search_keyword(keyword, category, max_pages)
                logger.info(f"Found {len(keyword_listings)} TCGPlayer listings for keyword: {keyword}")
                all_listings.extend(keyword_listings)
            except Exception as e:
                logger.error(f"Error searching TCGPlayer for keyword '{keyword}': {str(e)}")
        
        # Output count to console
        print(f"TCGPlayer scraper found {len(all_listings)} total listings")
        return all_listings
    
    async def _search_keyword(self, keyword: str, category: Optional[str] = None, max_pages: int = 2) -> List[Dict]:
        """Search for a specific keyword and collect listings from multiple pages"""
        listings = []
        
        # Determine the search URL based on category
        if category:
            search_url = f"https://www.tcgplayer.com/search/{category}/product"
        else:
            search_url = self.base_url
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{search_url}?q={quote(keyword)}&page={page}"
                
                # Update headers with a new user agent
                self.headers["User-Agent"] = self._get_next_user_agent()
                
                async with self.session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.warning(f"TCGPlayer returned status code {response.status} for keyword '{keyword}', page {page}")
                        continue
                    
                    html_content = await response.text()
                    
                    # Parse HTML content
                    page_listings = self._parse_tcgplayer_search_results(html_content, keyword, category)
                    listings.extend(page_listings)
                    
                    # Respect TCGPlayer's rate limits
                    await asyncio.sleep(2)  # Delay between page requests
            
            except Exception as e:
                logger.error(f"Error fetching TCGPlayer page {page} for keyword '{keyword}': {str(e)}")
                continue
        
        return listings
    
    def _parse_tcgplayer_search_results(self, html_content: str, keyword: str, category: Optional[str]) -> List[Dict]:
        """Parse TCGPlayer search results HTML to extract product listings"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers
        product_containers = soup.select('div.search-result')
        
        for container in product_containers:
            try:
                # Extract product URL and ID
                url_element = container.select_one('a.search-result__title')
                relative_url = url_element.get('href', '') if url_element else ""
                url = f"https://www.tcgplayer.com{relative_url}" if relative_url.startswith('/') else relative_url
                
                # Extract ID from URL
                listing_id = relative_url.split('/')[-1] if relative_url else ""
                
                # Extract product title
                title = url_element.text.strip() if url_element else "Unknown Title"
                
                # Extract price
                price_element = container.select_one('span.search-result__market-price--value')
                if not price_element:
                    price_element = container.select_one('div.inventory__price-with-shipping span')
                
                price_str = price_element.text.strip() if price_element else "0"
                price = self._extract_price(price_str)
                
                # Skip if no valid price found
                if price <= 0:
                    continue
                
                # Extract image URL
                image_element = container.select_one('img.search-result__image')
                image_url = image_element.get('src', '') if image_element else ""
                
                # Extract set information if available
                set_element = container.select_one('p.search-result__subtitle')
                set_info = set_element.text.strip() if set_element else ""
                
                # Extract rarity if available
                rarity_element = container.select_one('span.search-result__rarity')
                rarity = rarity_element.text.strip() if rarity_element else ""
                
                listing = {
                    "marketplace": "tcgplayer",
                    "listing_id": listing_id,
                    "title": title,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "set_info": set_info,
                    "rarity": rarity,
                    "category": category,
                    "source_keyword": keyword,
                    "timestamp": datetime.now().isoformat()
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing TCGPlayer product container: {str(e)}")
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
    
    async def get_product_details(self, listing_id: str, category: Optional[str] = None) -> Dict:
        """Get detailed information about a specific TCGPlayer product by listing ID"""
        await self.initialize()
        
        try:
            # Construct URL based on the category if provided
            if category:
                url = f"https://www.tcgplayer.com/product/{listing_id}"
            else:
                url = f"https://www.tcgplayer.com/product/{listing_id}"
            
            # Update headers with a new user agent
            self.headers["User-Agent"] = self._get_next_user_agent()
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"TCGPlayer returned status code {response.status} for listing ID {listing_id}")
                    return {}
                
                html_content = await response.text()
                
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
            title_element = soup.select_one('h1.product-details__name')
            details["title"] = title_element.text.strip() if title_element else "Unknown Title"
            
            # Extract market price
            market_price_element = soup.select_one('div.product-details__marketplace-price span')
            if market_price_element:
                market_price_str = market_price_element.text.strip()
                details["market_price"] = self._extract_price(market_price_str)
            
            # Extract lowest price
            lowest_price_element = soup.select_one('div.price-point__data')
            if lowest_price_element:
                lowest_price_str = lowest_price_element.text.strip()
                details["lowest_price"] = self._extract_price(lowest_price_str)
            else:
                details["lowest_price"] = 0
            
            # Set price to the lowest available price
            details["price"] = details.get("lowest_price", 0) or details.get("market_price", 0)
            
            # Extract set information
            set_element = soup.select_one('span.product-details__set')
            details["set_info"] = set_element.text.strip() if set_element else ""
            
            # Extract rarity
            rarity_element = soup.select_one('span.product-details__rarity')
            details["rarity"] = rarity_element.text.strip() if rarity_element else ""
            
            # Extract main image URL
            image_element = soup.select_one('img.product-details__img')
            details["image_url"] = image_element.get('src', '') if image_element else ""
            
            # URL
            details["url"] = f"https://www.tcgplayer.com/product/{listing_id}"
            
            return details
        
        except Exception as e:
            logger.error(f"Error parsing TCGPlayer product details for listing ID {listing_id}: {str(e)}")
            return {}

"""
StockX marketplace scraper for FlipHawk arbitrage system.
This module handles scraping StockX for products based on keywords from the subcategories.
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
from comprehensive_keywords import generate_keywords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stockx_scraper')

@dataclass
class StockXListing:
    """Class to store StockX product listing information."""
    title: str
    lowest_ask: float
    highest_bid: float
    last_sale: Optional[float]
    retail_price: Optional[float]
    link: str
    image_url: str
    product_id: str
    condition: str = "New"
    style_id: Optional[str] = None
    colorway: Optional[str] = None
    release_date: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price_premium: Optional[float] = None
    price_premium_percentage: Optional[float] = None
    volatility: Optional[float] = None
    source: str = "StockX"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.lowest_ask,  # Use lowest ask as the primary price
            'lowest_ask': self.lowest_ask,
            'highest_bid': self.highest_bid,
            'last_sale': self.last_sale,
            'retail_price': self.retail_price,
            'link': self.link,
            'image_url': self.image_url,
            'product_id': self.product_id,
            'condition': self.condition,
            'style_id': self.style_id,
            'colorway': self.colorway,
            'release_date': self.release_date,
            'brand': self.brand,
            'category': self.category,
            'subcategory': self.subcategory,
            'price_premium': self.price_premium,
            'price_premium_percentage': self.price_premium_percentage,
            'volatility': self.volatility,
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
        if self.style_id:
            models.append(self.style_id.lower())
            
        for pattern in model_patterns:
            matches = re.findall(pattern, title)
            models.extend(matches)
        
        # Remove duplicate models
        models = list(set(models))
        
        # If models found, prioritize them in the normalized title
        if models:
            title = ' '.join(models) + ' ' + title
            
        # Add colorway if available
        if self.colorway:
            title += ' ' + self.colorway.lower()
            
        # Add brand if available
        if self.brand:
            title += ' ' + self.brand.lower()
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class StockXScraper:
    """Class for scraping StockX product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.5):
        """
        Initialize the StockX scraper.
        
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
            'Referer': 'https://www.stockx.com/search',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1'
        }
        
        # Define categories on StockX
        self.categories = {
            "Sneakers": ["Sneakers", "Jordans", "Nike Dunks", "Yeezy", "Air Force 1", "New Balance"],
            "Streetwear": ["Streetwear", "Supreme", "BAPE", "Vintage Tees", "Band Tees", "Denim Jackets"],
            "Collectibles": ["Collectibles", "Trading Cards", "Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops"],
            "Electronics": ["Electronics", "Consoles", "Headphones", "Graphics Cards", "CPUs", "Gaming Accessories"],
            "Accessories": ["Watches", "Handbags", "Sunglasses", "Jewelry"]
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
                elif response.status == 429 or response.status == 403 or response.status == 503:  # Rate limited or blocked
                    delay = (2 ** retries) * self.delay_between_requests * 2  # Double the delay for StockX
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
    
    async def search_stockx(self, keyword: str, sort: str = "most-recent", max_pages: int = 2) -> List[StockXListing]:
        """
        Search StockX for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "most-recent", "most-popular", "highest-bid", "lowest-ask"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[StockXListing]: List of found listings
        """
        logger.info(f"Searching StockX for '{keyword}' with sort={sort}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "most-recent": "release_date",
            "most-popular": "most-active",
            "highest-bid": "highest-bid",
            "lowest-ask": "lowest-ask"
        }.get(sort, "release_date")
        
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL for the search
            url = f"https://stockx.com/search/sneakers?s={encoded_keyword}&sort={sort_param}&page={page}"
            
            logger.info(f"Fetching page {page} for keyword '{keyword}'")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_stockx_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page} for keyword '{keyword}'")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page} for keyword '{keyword}'")
            
            # If we have fewer listings than expected, we might have reached the end
            if len(page_listings) < 20:  # StockX typically shows 20 items per page
                break
        
        logger.info(f"Total of {len(listings)} listings found for keyword '{keyword}'")
        return listings
    
    def _parse_stockx_search_results(self, html: str) -> List[StockXListing]:
        """
        Parse StockX search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            
        Returns:
            List[StockXListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all search result items
        # StockX uses different selectors over time, so we try a few common ones
        result_elements = soup.select('.css-1ibvugw-GridProductTileContainer, .tile, .css-1ij7qiq')
        
        for element in result_elements:
            try:
                # Extract product id (from data attribute or href)
                product_id = ""
                link_elem = element.select_one('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = "https://stockx.com" + link_elem['href']
                    # Extract product ID from link
                    product_id_match = re.search(r'/([^/]+)$', link_elem['href'])
                    if product_id_match:
                        product_id = product_id_match.group(1)
                else:
                    continue  # Skip if no link found
                
                # Extract title
                title_elem = element.select_one('.css-1ujovsi-ProductTitle, .title, .css-1oqt13y')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Extract image URL
                img_url = ""
                img_elem = element.select_one('img')
                if img_elem:
                    if 'src' in img_elem.attrs:
                        img_url = img_elem['src']
                    elif 'data-src' in img_elem.attrs:
                        img_url = img_elem['data-src']
                
                # Extract lowest ask
                lowest_ask = None
                ask_elem = element.select_one('.css-1nye3eo-PriceValue, .lowest-ask, .css-81kgqv')
                if ask_elem:
                    ask_text = ask_elem.text.strip()
                    ask_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', ask_text)
                    if ask_match:
                        try:
                            lowest_ask = float(ask_match.group(1).replace(',', ''))
                        except ValueError:
                            continue
                
                if lowest_ask is None:
                    continue  # Skip if no price found
                
                # Extract highest bid
                highest_bid = None
                bid_elem = element.select_one('.css-11otmb3-PriceValue, .highest-bid, .css-81kgqv')
                if bid_elem:
                    bid_text = bid_elem.text.strip()
                    bid_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', bid_text)
                    if bid_match:
                        try:
                            highest_bid = float(bid_match.group(1).replace(',', ''))
                        except ValueError:
                            highest_bid = 0
                
                # Extract last sale price
                last_sale = None
                sale_elem = element.select_one('.css-97c1pj-LastSaleValue, .last-sale-value, .css-81kgqv')
                if sale_elem:
                    sale_text = sale_elem.text.strip()
                    sale_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', sale_text)
                    if sale_match:
                        try:
                            last_sale = float(sale_match.group(1).replace(',', ''))
                        except ValueError:
                            last_sale = None
                
                # Create listing object
                listing = StockXListing(
                    title=title,
                    lowest_ask=lowest_ask,
                    highest_bid=highest_bid if highest_bid is not None else 0,
                    last_sale=last_sale,
                    retail_price=None,  # Typically found on product page
                    link=link,
                    image_url=img_url,
                    product_id=product_id
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing StockX listing: {str(e)}")
                continue
        
        return listings
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product.
        
        Args:
            product_url (str): StockX product URL
            
        Returns:
            Optional[Dict[str, Any]]: Product details, or None if not found
        """
        html = await self.fetch_page(product_url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('.css-1ou6bb2-HeaderTitle h1, .product-title h1')
        if title_elem:
            details['title'] = title_elem.text.strip()
        
        # Extract retail price
        retail_elem = soup.select_one('[data-testid="product-detail-retail price"], .retail-price, .detail-value')
        if retail_elem:
            retail_text = retail_elem.text.strip()
            retail_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', retail_text)
            if retail_match:
                try:
                    details['retail_price'] = float(retail_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract style ID (SKU)
        style_elem = soup.select_one('[data-testid="product-detail-style"], .style-id, .detail-value')
        if style_elem:
            details['style_id'] = style_elem.text.strip()
        
        # Extract colorway
        colorway_elem = soup.select_one('[data-testid="product-detail-colorway"], .colorway, .detail-value')
        if colorway_elem:
            details['colorway'] = colorway_elem.text.strip()
        
        # Extract release date
        release_elem = soup.select_one('[data-testid="product-detail-release date"], .release-date, .detail-value')
        if release_elem:
            details['release_date'] = release_elem.text.strip()
        
        # Extract brand
        brand_elem = soup.select_one('.css-15dnfyj, .brand-name, .detail-value')
        if brand_elem:
            details['brand'] = brand_elem.text.strip()
        
        # Extract price premium
        premium_elem = soup.select_one('.css-1utxbha-PriceValue, .price-premium, .detail-value')
        if premium_elem:
            premium_text = premium_elem.text.strip()
            premium_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', premium_text)
            if premium_match:
                try:
                    details['price_premium'] = float(premium_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            # Extract percentage
            percentage_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)%', premium_text)
            if percentage_match:
                try:
                    details['price_premium_percentage'] = float(percentage_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract current lowest ask
        ask_elem = soup.select_one('.css-yw9abi-PriceValue, .lowest-ask-value, .detail-value')
        if ask_elem:
            ask_text = ask_elem.text.strip()
            ask_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', ask_text)
            if ask_match:
                try:
                    details['lowest_ask'] = float(ask_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract highest bid
        bid_elem = soup.select_one('.css-1w4cawd-PriceValue, .highest-bid-value, .detail-value')
        if bid_elem:
            bid_text = bid_elem.text.strip()
            bid_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', bid_text)
            if bid_match:
                try:
                    details['highest_bid'] = float(bid_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract last sale
        sale_elem = soup.select_one('.css-1dvvx4-LastSaleValue, .last-sale-value, .detail-value')
        if sale_elem:
            sale_text = sale_elem.text.strip()
            sale_match = re.search(r'\$(\d+(?:,\d+)*(?:\.\d+)?)', sale_text)
            if sale_match:
                try:
                    details['last_sale'] = float(sale_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract volatility
        volatility_elem = soup.select_one('.css-1u6xl5o-VolatilityValue, .volatility-value, .detail-value')
        if volatility_elem:
            volatility_text = volatility_elem.text.strip()
            volatility_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)%', volatility_text)
            if volatility_match:
                try:
                    details['volatility'] = float(volatility_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract large image
        img_elem = soup.select_one('.css-18nj2pz-Image, .product-image img')
        if img_elem and 'src' in img_elem.attrs:
            details['image_url'] = img_elem['src']
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search StockX for products in a specific subcategory by generating keywords.
        
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
        pages_per_keyword = min(3, (max_listings_per_keyword + 19) // 20)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for most active listings
                popular_listings = await self.search_stockx(
                    keyword, 
                    sort="most-popular", 
                    max_pages=pages_per_keyword
                )
                
                # Search for listings by lowest ask
                low_ask_listings = await self.search_stockx(
                    keyword, 
                    sort="lowest-ask", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in popular_listings])
                all_listings.extend([listing.to_dict() for listing in low_ask_listings])
                
                logger.info(f"Found {len(popular_listings) + len(low_ask_listings)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                logger.error(f"Error searching StockX for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_stockx_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run StockX search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = StockXScraper(use_proxy=False, delay_between_requests=2.5)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching StockX for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing
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
    async def test_stockx_scraper():
        subcategories = ["Jordans", "Nike Dunks"]
        results = await run_stockx_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Lowest Ask: ${result['lowest_ask']:.2f}")
            if result.get('highest_bid'):
                print(f"Highest Bid: ${result['highest_bid']:.2f}")
            if result.get('last_sale'):
                print(f"Last Sale: ${result['last_sale']:.2f}")
            print(f"Link: {result['link']}")
    
    # Run the test
    asyncio.run(test_stockx_scraper())

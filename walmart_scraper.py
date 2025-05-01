"""
Walmart marketplace scraper for FlipHawk arbitrage system.
This module handles scraping Walmart for products based on keywords from the subcategories.
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
logger = logging.getLogger('walmart_scraper')

@dataclass
class WalmartListing:
    """Class to store Walmart product listing information."""
    title: str
    price: float
    original_price: Optional[float]
    link: str
    image_url: str
    rating: Optional[float]
    review_count: Optional[int]
    walmart_plus: bool
    item_id: str
    seller: Optional[str]
    condition: str = "New"
    free_shipping: bool = False
    shipping_cost: float = 0.0
    availability: str = "In Stock"
    features: List[str] = None
    categories: List[str] = None
    source: str = "Walmart"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        if self.features is None:
            features_list = []
        else:
            features_list = self.features
            
        if self.categories is None:
            categories_list = []
        else:
            categories_list = self.categories
        
        return {
            'title': self.title,
            'price': self.price,
            'original_price': self.original_price,
            'link': self.link,
            'image_url': self.image_url,
            'rating': self.rating,
            'review_count': self.review_count,
            'walmart_plus': self.walmart_plus,
            'item_id': self.item_id,
            'seller': self.seller,
            'condition': self.condition,
            'free_shipping': self.free_shipping,
            'shipping_cost': self.shipping_cost,
            'availability': self.availability,
            'features': features_list,
            'categories': categories_list,
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


class WalmartScraper:
    """Class for scraping Walmart product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the Walmart scraper.
        
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
            'Referer': 'https://www.walmart.com/',
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
                elif response.status == 429 or response.status == 503:  # Rate limited or service unavailable
                    delay = (2 ** retries) * self.delay_between_requests
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
    
    async def search_walmart(self, keyword: str, sort: str = "price_low", max_pages: int = 2) -> List[WalmartListing]:
        """
        Search Walmart for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "price_low", "price_high", "best_match", "best_seller", "newest"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[WalmartListing]: List of found listings
        """
        logger.info(f"Searching Walmart for '{keyword}' with sort={sort}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "price_low": "price_low",
            "price_high": "price_high",
            "best_match": "best_match",
            "best_seller": "best_seller",
            "newest": "newest"
        }.get(sort, "best_match")
        
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL for the search
            url = f"https://www.walmart.com/search?q={encoded_keyword}&sort={sort_param}"
            if page > 1:
                url += f"&page={page}"
            
            logger.info(f"Fetching page {page} for keyword '{keyword}'")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_walmart_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page} for keyword '{keyword}'")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page} for keyword '{keyword}'")
            
            # If we have fewer listings than expected, we might have reached the end
            if len(page_listings) < 20:
                break
        
        logger.info(f"Total of {len(listings)} listings found for keyword '{keyword}'")
        return listings
    
    def _parse_walmart_search_results(self, html: str) -> List[WalmartListing]:
        """
        Parse Walmart search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            
        Returns:
            List[WalmartListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Updated selectors to handle Walmart's current structure
        product_tiles = soup.select('div[data-item-id], div.product-item, div[data-automation-id="product"]')
        
        if not product_tiles:
            # Fallback to more generic selectors if specific ones don't work
            product_tiles = soup.select('.search-result-gridview-item, .Grid-col, [data-testid="list-view"]')
        
        for product in product_tiles:
            try:
                # Extract item ID
                item_id = product.get('data-item-id') or product.get('data-product-id') or ''
                if not item_id:
                    # Try finding ID in other attributes
                    for attr in product.attrs:
                        if 'item' in attr or 'product' in attr and 'id' in attr:
                            item_id = product.get(attr, '')
                            break
                
                # Skip if no ID found
                if not item_id:
                    continue
                
                # Extract title
                title_elem = product.select_one('span.product-title-text, .product-title, [data-automation-id="product-title"], h3, h2')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                if not title:
                    continue
                
                # Extract link
                link_elem = product.select_one('a[href*="/ip/"], a.product-title-link, a[data-automation-id="product-title-link"]')
                if not link_elem or 'href' not in link_elem.attrs:
                    continue
                
                link = link_elem['href']
                if link.startswith('/'):
                    link = f'https://www.walmart.com{link}'
                
                # Extract price
                price_elem = product.select_one('span.price-main, .product-price-amount, [data-automation-id="product-price"], .price')
                if not price_elem:
                    continue
                
                price_text = price_elem.text.strip()
                price_match = re.search(r'\$?(\d+(?:\.\d+)?)', price_text)
                if not price_match:
                    continue
                
                try:
                    price = float(price_match.group(1))
                except ValueError:
                    continue
                
                # Extract original price if on sale
                original_price = None
                was_price_elem = product.select_one('.was-price, .strike-through-price, [data-automation-id="strikethrough-price"]')
                if was_price_elem:
                    was_price_text = was_price_elem.text.strip()
                    was_price_match = re.search(r'\$?(\d+(?:\.\d+)?)', was_price_text)
                    if was_price_match:
                        try:
                            original_price = float(was_price_match.group(1))
                        except ValueError:
                            pass
                
                # Extract image URL
                img_url = ""
                img_elem = product.select_one('img')
                if img_elem:
                    if 'src' in img_elem.attrs and img_elem['src'] != '':
                        img_url = img_elem['src']
                    elif 'data-src' in img_elem.attrs and img_elem['data-src'] != '':
                        img_url = img_elem['data-src']
                    elif 'srcset' in img_elem.attrs:
                        srcset = img_elem['srcset'].split(',')[0]
                        img_url = srcset.strip().split(' ')[0]
                
                # Extract rating
                rating = None
                rating_elem = product.select_one('[aria-label*="out of"], .stars-container')
                if rating_elem:
                    rating_text = rating_elem.get('aria-label') or rating_elem.text
                    rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:out of|\/)\s*\d+', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                        except ValueError:
                            pass
                
                # Extract review count
                review_count = None
                reviews_elem = product.select_one('[aria-label*="reviews"], .reviews-count')
                if reviews_elem:
                    reviews_text = reviews_elem.text.strip()
                    review_match = re.search(r'(\d+)\s*reviews', reviews_text)
                    if review_match:
                        try:
                            review_count = int(review_match.group(1))
                        except ValueError:
                            pass
                
                # Check for Walmart+
                walmart_plus = False
                plus_elem = product.select_one('.walmart-plus, .wplus-icon, [aria-label*="Walmart+"]')
                if plus_elem:
                    walmart_plus = True
                
                # Extract shipping info
                free_shipping = False
                shipping_cost = 0.0
                shipping_elem = product.select_one('.fulfillment-shipping-text, .free-shipping, [data-automation-id="shipping-text"]')
                if shipping_elem:
                    shipping_text = shipping_elem.text.strip().lower()
                    if 'free' in shipping_text:
                        free_shipping = True
                    else:
                        shipping_match = re.search(r'\$(\d+(?:\.\d+)?)', shipping_text)
                        if shipping_match:
                            try:
                                shipping_cost = float(shipping_match.group(1))
                            except ValueError:
                                shipping_cost = 0.0
                
                # Extract seller info
                seller = None
                seller_elem = product.select_one('.seller-name, .product-seller, [data-automation-id="seller-name"]')
                if seller_elem:
                    seller = seller_elem.text.strip()
                
                # Create listing object
                listing = WalmartListing(
                    title=title,
                    price=price,
                    original_price=original_price,
                    link=link,
                    image_url=img_url,
                    rating=rating,
                    review_count=review_count,
                    walmart_plus=walmart_plus,
                    item_id=item_id,
                    seller=seller,
                    free_shipping=free_shipping,
                    shipping_cost=shipping_cost,
                    features=[],
                    categories=[]
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing Walmart listing: {str(e)}")
                continue
        
        return listings
    
    async def get_product_details(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product.
        
        Args:
            url (str): Walmart product URL
            
        Returns:
            Optional[Dict[str, Any]]: Product details, or None if not found
        """
        html = await self.fetch_page(url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('h1.prod-ProductTitle, [data-automation-id="product-title"]')
        if title_elem:
            details['title'] = title_elem.text.strip()
        
        # Extract price
        price_elem = soup.select_one('.price-characteristic, [data-automation-id="product-price"]')
        if price_elem:
            price_text = price_elem.text.strip() if not price_elem.get('content') else price_elem.get('content')
            price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
            if price_match:
                try:
                    details['price'] = float(price_match.group(1))
                except ValueError:
                    pass
        
        # Extract product features
        features = []
        feature_elems = soup.select('#product-overview li, .about-product li, [data-automation-id="product-description"] li')
        for elem in feature_elems:
            feature = elem.text.strip()
            if feature:
                features.append(feature)
        
        if features:
            details['features'] = features
        
        # Extract specifications
        specs = {}
        spec_rows = soup.select('.specifications-container tr, .product-specifications tr')
        for row in spec_rows:
            cells = row.select('td, th')
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                if key and value:
                    specs[key] = value
        
        if specs:
            details['specifications'] = specs
        
        # Extract seller info
        seller_elem = soup.select_one('.seller-name, [data-automation-id="seller-name"]')
        if seller_elem:
            details['seller'] = seller_elem.text.strip()
        
        # Extract shipping info
        shipping_elem = soup.select_one('.fulfillment-shipping-text, [data-automation-id="shipping-text"]')
        if shipping_elem:
            shipping_text = shipping_elem.text.strip().lower()
            details['free_shipping'] = 'free' in shipping_text
            if not details.get('free_shipping'):
                shipping_match = re.search(r'\$(\d+(?:\.\d+)?)', shipping_text)
                if shipping_match:
                    try:
                        details['shipping_cost'] = float(shipping_match.group(1))
                    except ValueError:
                        details['shipping_cost'] = 0.0
        
        # Extract product images
        images = []
        img_elems = soup.select('.prod-hero-image img, .carousel-img, [data-automation-id="image-gallery"] img')
        for img in img_elems:
            src = img.get('src') or img.get('data-src') or ''
            if src and src not in images:
                # Get full-size image when possible
                src = re.sub(r'\d+X\d+', '1000X1000', src)
                images.append(src)
        
        if images:
            details['images'] = images
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search Walmart for products in a specific subcategory by generating keywords.
        
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
                # Search for low-priced items first (for buying)
                low_priced = await self.search_walmart(
                    keyword, 
                    sort="price_low", 
                    max_pages=pages_per_keyword
                )
                
                # Also search for high-priced items (for selling)
                high_priced = await self.search_walmart(
                    keyword, 
                    sort="price_high", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in high_priced])
                
                logger.info(f"Found {len(low_priced) + len(high_priced)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Walmart for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_walmart_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Walmart search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = WalmartScraper(use_proxy=False, delay_between_requests=2.0)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Walmart for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing
                for listing in listings:
                    listing['subcategory'] = subcategory
                
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings for subcategory: {subcategory}")
                
                # Avoid hitting rate limits between subcategories
                await asyncio.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                logger.error(f"Error processing subcategory '{subcategory}': {str(e)}")
                continue
        
        logger.info(f"Total of {len(all_listings)} listings found across all subcategories")
        return all_listings
        
    finally:
        await scraper.close_session()

# Entry point for direct execution
if __name__ == "__main__":
    async def test_walmart_scraper():
        subcategories = ["Headphones", "Keyboards"]
        results = await run_walmart_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
    
    # Run the test
    asyncio.run(test_walmart_scraper())


"""
Amazon marketplace scraper for FlipHawk arbitrage system.
This module handles scraping Amazon for products based on keywords from the subcategories.
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
logger = logging.getLogger('amazon_scraper')

@dataclass
class AmazonListing:
    """Class to store Amazon product listing information."""
    title: str
    price: float
    original_price: Optional[float]
    link: str
    image_url: str
    rating: Optional[float]
    review_count: Optional[int]
    is_prime: bool
    asin: str
    seller: Optional[str]
    condition: str = "New"
    free_shipping: bool = False
    shipping_cost: float = 0.0
    availability: str = "In Stock"
    features: List[str] = None
    categories: List[str] = None
    source: str = "Amazon"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        features_list = self.features if self.features else []
        categories_list = self.categories if self.categories else []
        
        return {
            'title': self.title,
            'price': self.price,
            'original_price': self.original_price,
            'link': self.link,
            'image_url': self.image_url,
            'rating': self.rating,
            'review_count': self.review_count,
            'is_prime': self.is_prime,
            'asin': self.asin,
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


class AmazonScraper:
    """Class for scraping Amazon product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the Amazon scraper.
        
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
            'Referer': 'https://www.amazon.com/',
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
    
    async def search_amazon(self, keyword: str, sort: str = "price-asc", max_pages: int = 2) -> List[AmazonListing]:
        """
        Search Amazon for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "price-asc", "price-desc", "relevance", "review-rank"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[AmazonListing]: List of found listings
        """
        logger.info(f"Searching Amazon for '{keyword}' with sort={sort}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "price-asc": "price-asc-rank",
            "price-desc": "price-desc-rank",
            "relevance": "relevance-rank",
            "review-rank": "review-rank",
            "newest": "date-desc-rank"
        }.get(sort, "relevance-rank")
        
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL for the search
            url = f"https://www.amazon.com/s?k={encoded_keyword}&s={sort_param}"
            if page > 1:
                url += f"&page={page}"
            
            logger.info(f"Fetching page {page} for keyword '{keyword}'")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_amazon_search_results(html)
            
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
    
    def _parse_amazon_search_results(self, html: str) -> List[AmazonListing]:
        """
        Parse Amazon search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            
        Returns:
            List[AmazonListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all search result items
        result_elements = soup.select('div[data-component-type="s-search-result"]')
        
        for element in result_elements:
            try:
                # Skip sponsored products if desired
                if element.select_one('.s-sponsored-label-info-icon'):
                    continue
                
                # Extract ASIN (Amazon Standard Identification Number)
                asin = element.get('data-asin')
                if not asin:
                    continue
                
                # Extract title
                title_elem = element.select_one('h2 a span')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Extract link
                link_elem = element.select_one('h2 a')
                link = f"https://www.amazon.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else ""
                
                # Extract price
                price = None
                original_price = None
                
                price_whole_elem = element.select_one('.a-price-whole')
                price_fraction_elem = element.select_one('.a-price-fraction')
                
                if price_whole_elem and price_fraction_elem:
                    try:
                        price_whole = price_whole_elem.text.strip().replace(',', '')
                        price_fraction = price_fraction_elem.text.strip()
                        price = float(f"{price_whole}.{price_fraction}")
                    except ValueError:
                        continue
                
                # Sometimes there's an original "was" price
                was_price_elem = element.select_one('.a-text-price .a-offscreen')
                if was_price_elem:
                    original_price_text = was_price_elem.text.strip()
                    try:
                        original_price = float(original_price_text.replace(', ', '').replace(',', ''))
                    except ValueError:
                        pass
                
                # If we couldn't find a price, skip this listing
                if price is None:
                    continue
                
                # Extract image URL
                img_elem = element.select_one('img.s-image')
                img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                
                # Extract rating
                rating = None
                rating_elem = element.select_one('i.a-icon-star-small')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    try:
                        rating = float(rating_text.split(' ')[0].replace(',', '.'))
                    except (ValueError, IndexError):
                        pass
                
                # Extract review count
                review_count = None
                review_count_elem = element.select_one('span[aria-label*="stars"]')
                if review_count_elem:
                    try:
                        review_text = review_count_elem.get('aria-label', '')
                        review_count_match = re.search(r'([\d,]+)\s+reviews', review_text)
                        if review_count_match:
                            review_count = int(review_count_match.group(1).replace(',', ''))
                    except (ValueError, AttributeError):
                        pass
                
                # Extract Prime status
                is_prime = bool(element.select_one('i.a-icon-prime'))
                
                # Extract shipping info
                free_shipping = False
                shipping_cost = 0.0
                shipping_elem = element.select_one('.a-row.a-size-base span:contains("FREE Shipping")')
                if shipping_elem:
                    free_shipping = True
                else:
                    shipping_text_elem = element.select_one('.a-row.a-size-base span:contains("Shipping")')
                    if shipping_text_elem:
                        shipping_text = shipping_text_elem.text.strip()
                        shipping_match = re.search(r'\$(\d+\.\d+)', shipping_text)
                        if shipping_match:
                            shipping_cost = float(shipping_match.group(1))
                
                # Extract seller info if available
                seller = None
                seller_elem = element.select_one('.a-row.a-size-base:contains("by")')
                if seller_elem:
                    seller_text = seller_elem.text.strip()
                    seller_match = re.search(r'by\s+(.+)', seller_text)
                    if seller_match:
                        seller = seller_match.group(1).strip()
                
                # Create listing object
                listing = AmazonListing(
                    title=title,
                    price=price,
                    original_price=original_price,
                    link=link,
                    image_url=img_url,
                    rating=rating,
                    review_count=review_count,
                    is_prime=is_prime,
                    asin=asin,
                    seller=seller,
                    free_shipping=free_shipping,
                    shipping_cost=shipping_cost
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing Amazon listing: {str(e)}")
                continue
        
        return listings
    
    async def get_product_details(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product by ASIN.
        
        Args:
            asin (str): Amazon Standard Identification Number
            
        Returns:
            Optional[Dict[str, Any]]: Product details, or None if not found
        """
        url = f"https://www.amazon.com/dp/{asin}"
        html = await self.fetch_page(url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('#productTitle')
        if title_elem:
            details['title'] = title_elem.text.strip()
        
        # Extract price
        price_elem = soup.select_one('#priceblock_ourprice, #priceblock_saleprice, .a-price .a-offscreen')
        if price_elem:
            price_text = price_elem.text.strip()
            try:
                details['price'] = float(price_text.replace(', ', '').replace(',', ''))
            except ValueError:
                pass
        
        # Extract features
        features = []
        feature_elems = soup.select('#feature-bullets ul li span.a-list-item')
        for elem in feature_elems:
            feature_text = elem.text.strip()
            if feature_text:
                features.append(feature_text)
        
        if features:
            details['features'] = features
        
        # Extract category
        categories = []
        breadcrumb_elems = soup.select('#wayfinding-breadcrumbs_feature_div ul li a')
        for elem in breadcrumb_elems:
            category_text = elem.text.strip()
            if category_text:
                categories.append(category_text)
        
        if categories:
            details['categories'] = categories
        
        # Extract availability
        availability_elem = soup.select_one('#availability span')
        if availability_elem:
            details['availability'] = availability_elem.text.strip()
        
        # Extract description
        description_elem = soup.select_one('#productDescription p')
        if description_elem:
            details['description'] = description_elem.text.strip()
        
        # Extract images
        image_elem = soup.select_one('#landingImage')
        if image_elem and 'data-old-hires' in image_elem.attrs:
            details['image_url'] = image_elem['data-old-hires']
        elif image_elem and 'src' in image_elem.attrs:
            details['image_url'] = image_elem['src']
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search Amazon for products in a specific subcategory by generating keywords.
        
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
        pages_per_keyword = min(5, (max_listings_per_keyword + 19) // 20)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self.search_amazon(keyword, sort="price-asc", max_pages=pages_per_keyword)
                
                # If we need more, search for high-priced items (for selling)
                if len(low_priced) < max_listings_per_keyword:
                    high_priced = await self.search_amazon(keyword, sort="price-desc", max_pages=pages_per_keyword)
                    all_listings.extend([listing.to_dict() for listing in low_priced])
                    all_listings.extend([listing.to_dict() for listing in high_priced])
                else:
                    all_listings.extend([listing.to_dict() for listing in low_priced])
                
                logger.info(f"Found {len(all_listings)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Amazon for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_amazon_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Amazon search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = AmazonScraper(use_proxy=False, delay_between_requests=2.0)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Amazon for subcategory: {subcategory}")
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
    async def test_amazon_scraper():
        subcategories = ["Headphones", "Mechanical Keyboards"]
        results = await run_amazon_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
    
    # Run the test
    asyncio.run(test_amazon_scraper())

"""
eBay marketplace scraper for FlipHawk arbitrage system.
This module handles scraping eBay for products based on keywords from the subcategories.
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
logger = logging.getLogger('ebay_scraper')

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


class EbayScraper:
    """Class for scraping eBay product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=1.5):
        """
        Initialize the eBay scraper.
        
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
    
    async def search_ebay(self, keyword: str, sort: str = "price_asc", min_price: float = None, max_price: float = None, max_pages: int = 2) -> List[EbayListing]:
        """
        Search eBay for a keyword with sorting and price filtering options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "price_asc", "price_desc", "newly_listed", "ending_soonest"
            min_price (float): Minimum price filter
            max_price (float): Maximum price filter
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[EbayListing]: List of found listings
        """
        logger.info(f"Searching eBay for '{keyword}' with sort={sort}, min_price={min_price}, max_price={max_price}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "price_asc": "15",
            "price_desc": "16",
            "newly_listed": "10",
            "ending_soonest": "1",
            "best_match": "12"
        }.get(sort, "12")
        
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL for the search
            url_parts = [
                f"https://www.ebay.com/sch/i.html?_nkw={encoded_keyword}",
                f"_sop={sort_param}",
                "LH_BIN=1",  # Buy It Now only
                "rt=nc",  # Non-category specific search
                "_ipg=240"  # 240 items per page (maximum)
            ]
            
            # Add price filters if specified
            if min_price is not None:
                url_parts.append(f"_udlo={min_price}")
            if max_price is not None:
                url_parts.append(f"_udhi={max_price}")
            
            # Add page number if not the first page
            if page > 1:
                url_parts.append(f"_pgn={page}")
            
            url = "&".join(url_parts)
            
            logger.info(f"Fetching page {page} for keyword '{keyword}'")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_ebay_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page} for keyword '{keyword}'")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page} for keyword '{keyword}'")
            
            # If we have fewer listings than expected, we might have reached the end
            if len(page_listings) < 50:
                break
        
        logger.info(f"Total of {len(listings)} listings found for keyword '{keyword}'")
        return listings
    
    def _parse_ebay_search_results(self, html: str) -> List[EbayListing]:
        """
        Parse eBay search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            
        Returns:
            List[EbayListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all search result items
        result_elements = soup.select('li.s-item')
        
        for element in result_elements:
            try:
                # Skip the first element which is often a search result header
                if 'srp-river-results-SEARCH_STATUS' in element.get('class', []):
                    continue
                
                # Extract title
                title_elem = element.select_one('.s-item__title')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                if title.lower() == 'shop on ebay':
                    continue  # Skip header items
                
                # Extract price
                price_elem = element.select_one('.s-item__price')
                if not price_elem:
                    continue
                
                price_text = price_elem.text.strip()
                
                # Handle price ranges - take the lower price
                if ' to ' in price_text:
                    price_match = re.search(r'\$([0-9,]+\.\d+)', price_text)
                    if not price_match:
                        continue
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
                else:
                    price_match = re.search(r'\$([0-9,]+\.\d+)', price_text)
                    if not price_match:
                        continue
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
                
                # Extract link
                link_elem = element.select_one('a.s-item__link')
                if not link_elem or 'href' not in link_elem.attrs:
                    continue
                
                link = link_elem['href'].split('?')[0]  # Remove URL parameters
                
                # Extract item ID from the link
                item_id_match = re.search(r'/(\d+)\?', link_elem['href'])
                item_id = item_id_match.group(1) if item_id_match else ""
                
                # Extract image
                img_elem = element.select_one('.s-item__image-img')
                img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                
                # Extract shipping info
                shipping_elem = element.select_one('.s-item__shipping, .s-item__freeXDays, .s-item__logisticsCost')
                shipping_text = shipping_elem.get_text(strip=True) if shipping_elem else ""
                free_shipping = 'Free' in shipping_text
                
                shipping_cost = 0.0
                if not free_shipping and shipping_elem:
                    shipping_match = re.search(r'\$?(\d+\.\d+)', shipping_text)
                    if shipping_match:
                        try:
                            shipping_cost = float(shipping_match.group(1))
                        except ValueError:
                            shipping_cost = 0.0
                
                # Extract condition
                condition_elem = element.select_one('.SECONDARY_INFO')
                condition = condition_elem.get_text(strip=True) if condition_elem else "New"
                
                # Extract location
                location_elem = element.select_one('.s-item__location')
                location = location_elem.get_text(strip=True) if location_elem else None
                
                # Extract seller information (when available)
                seller_rating = None
                seller_feedback = None
                seller_elem = element.select_one('.s-item__seller-info-text')
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    # Extract feedback score
                    feedback_match = re.search(r'(\d+(?:,\d+)*)\s+\(', seller_text)
                    if feedback_match:
                        try:
                            seller_feedback = int(feedback_match.group(1).replace(',', ''))
                        except ValueError:
                            seller_feedback = None
                    
                    # Extract feedback percentage
                    rating_match = re.search(r'\((\d+(?:\.\d+)?)%\)', seller_text)
                    if rating_match:
                        try:
                            seller_rating = float(rating_match.group(1))
                        except ValueError:
                            seller_rating = None
                
                # Extract sold count
                sold_count = 0
                sold_elem = element.select_one('.s-item__quantitySold, .s-item__hotness')
                if sold_elem:
                    sold_text = sold_elem.get_text(strip=True)
                    sold_match = re.search(r'(\d+(?:,\d+)*)\s+sold', sold_text, re.IGNORECASE)
                    if sold_match:
                        try:
                            sold_count = int(sold_match.group(1).replace(',', ''))
                        except ValueError:
                            sold_count = 0
                
                # Extract watchers
                watchers = None
                watchers_elem = element.select_one('.s-item__watchCount')
                if watchers_elem:
                    watchers_text = watchers_elem.get_text(strip=True)
                    watchers_match = re.search(r'(\d+(?:,\d+)*)', watchers_text)
                    if watchers_match:
                        try:
                            watchers = int(watchers_match.group(1).replace(',', ''))
                        except ValueError:
                            watchers = None
                
                # Extract time left (for auctions)
                time_left = None
                time_elem = element.select_one('.s-item__time-left')
                if time_elem:
                    time_left = time_elem.get_text(strip=True)
                
                # Create listing object
                listing = EbayListing(
                    title=title,
                    price=price,
                    link=link,
                    image_url=img_url,
                    free_shipping=free_shipping,
                    shipping_cost=shipping_cost,
                    seller_rating=seller_rating,
                    seller_feedback=seller_feedback,
                    item_id=item_id,
                    condition=condition,
                    location=location,
                    sold_count=sold_count,
                    watchers=watchers,
                    time_left=time_left
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing eBay listing: {str(e)}")
                continue
        
        return listings
    
    async def get_item_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific item by ID.
        
        Args:
            item_id (str): eBay item ID
            
        Returns:
            Optional[Dict[str, Any]]: Item details, or None if not found
        """
        url = f"https://www.ebay.com/itm/{item_id}"
        html = await self.fetch_page(url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('#itemTitle')
        if title_elem:
            # Remove "Details about" prefix
            title_text = title_elem.get_text(strip=True)
            title = re.sub(r'^Details about\s+', '', title_text)
            details['title'] = title
        
        # Extract current price
        price_elem = soup.select_one('#prcIsum')
        if price_elem and 'content' in price_elem.attrs:
            try:
                details['price'] = float(price_elem['content'])
            except ValueError:
                pass
        
        # Extract item specifics
        item_specifics = {}
        specifics_elems = soup.select('.ux-labels-values__labels')
        for elem in specifics_elems:
            label = elem.get_text(strip=True)
            value_elem = elem.find_next_sibling('.ux-labels-values__values')
            if value_elem:
                value = value_elem.get_text(strip=True)
                item_specifics[label] = value
        
        if item_specifics:
            details['item_specifics'] = item_specifics
        
        # Extract description
        iframe_elem = soup.select_one('#desc_ifr')
        if iframe_elem and 'src' in iframe_elem.attrs:
            desc_url = iframe_elem['src']
            desc_html = await self.fetch_page(desc_url)
            if desc_html:
                desc_soup = BeautifulSoup(desc_html, 'html.parser')
                details['description'] = desc_soup.get_text(strip=True)
        
        # Extract seller information
        seller_info = {}
        seller_username_elem = soup.select_one('.ux-seller-section__item--username a')
        if seller_username_elem:
            seller_info['username'] = seller_username_elem.get_text(strip=True)
            
        feedback_score_elem = soup.select_one('span.ux-textspans--SECONDARY.ux-textspans--BOLD')
        if feedback_score_elem:
            feedback_text = feedback_score_elem.get_text(strip=True)
            feedback_match = re.search(r'(\d+(?:,\d+)*)', feedback_text)
            if feedback_match:
                try:
                    seller_info['feedback_score'] = int(feedback_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        positive_feedback_elem = soup.select_one('.ux-seller-section__item--feedback span')
        if positive_feedback_elem:
            feedback_text = positive_feedback_elem.get_text(strip=True)
            feedback_match = re.search(r'([\d.]+)%', feedback_text)
            if feedback_match:
                try:
                    seller_info['positive_feedback_percent'] = float(feedback_match.group(1))
                except ValueError:
                    pass
        
        if seller_info:
            details['seller_info'] = seller_info
        
        # Extract shipping information
        shipping_info = {}
        shipping_cost_elem = soup.select_one('#shSummary')
        if shipping_cost_elem:
            shipping_text = shipping_cost_elem.get_text(strip=True)
            free_shipping_match = re.search(r'FREE', shipping_text, re.IGNORECASE)
            if free_shipping_match:
                shipping_info['free_shipping'] = True
                shipping_info['shipping_cost'] = 0.0
            else:
                shipping_match = re.search(r'\$(\d+\.\d+)', shipping_text)
                if shipping_match:
                    try:
                        shipping_info['shipping_cost'] = float(shipping_match.group(1))
                        shipping_info['free_shipping'] = False
                    except ValueError:
                        pass
        
        if shipping_info:
            details['shipping_info'] = shipping_info
        
        # Extract return policy
        return_policy = {}
        return_elem = soup.select_one('#vi-ret-accrd-txt span')
        if return_elem:
            return_text = return_elem.get_text(strip=True)
            details['returns_accepted'] = 'not accepted' not in return_text.lower()
            return_policy['policy'] = return_text
        
        if return_policy:
            details['return_policy'] = return_policy
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search eBay for products in a specific subcategory by generating keywords.
        
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
        pages_per_keyword = min(3, (max_listings_per_keyword + 239) // 240)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self.search_ebay(
                    keyword, 
                    sort="price_asc", 
                    max_pages=pages_per_keyword
                )
                
                # If we want more, search for high-priced items (for selling)
                high_priced = await self.search_ebay(
                    keyword, 
                    sort="price_desc", 
                    max_pages=pages_per_keyword
                )
                
                # Add to the combined list
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in high_priced])
                
                logger.info(f"Found {len(low_priced) + len(high_priced)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching eBay for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_ebay_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run eBay search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = EbayScraper(use_proxy=False, delay_between_requests=1.5)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching eBay for subcategory: {subcategory}")
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
    async def test_ebay_scraper():
        subcategories = ["Headphones", "Mechanical Keyboards"]
        results = await run_ebay_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
    
    # Run the test
    asyncio.run(test_ebay_scraper())

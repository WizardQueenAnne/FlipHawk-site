"""
Facebook Marketplace scraper for FlipHawk arbitrage system.
This module handles scraping Facebook Marketplace for products based on keywords from the subcategories.
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
from typing import List, Dict, Any, Optional
from comprehensive_keywords import generate_keywords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('facebook_scraper')

@dataclass
class FacebookListing:
    """Class to store Facebook Marketplace product listing information."""
    title: str
    price: float
    link: str
    image_url: str
    condition: str
    location: Optional[str]
    seller_name: Optional[str]
    posting_date: Optional[str]
    description: Optional[str]
    listing_id: str
    shipping_available: bool = False
    local_pickup: bool = True
    category: Optional[str] = None
    source: str = "Facebook Marketplace"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'link': self.link,
            'image_url': self.image_url,
            'condition': self.condition,
            'location': self.location,
            'seller_name': self.seller_name,
            'posting_date': self.posting_date,
            'description': self.description,
            'listing_id': self.listing_id,
            'shipping_available': self.shipping_available,
            'local_pickup': self.local_pickup,
            'category': self.category,
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
        
        # Add condition
        if self.condition and self.condition.lower() not in title:
            title += ' ' + self.condition.lower()
        
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title


class FacebookScraper:
    """Class for scraping Facebook Marketplace product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the Facebook Marketplace scraper.
        
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
            'Referer': 'https://www.facebook.com/marketplace/',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'cache-control': 'max-age=0'
        }
        
        # Define location data (defaults to US nationwide)
        self.location = {
            'country': 'United States',
            'latitude': 37.0902,
            'longitude': -95.7129,
            'radius': 100  # miles
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
                elif response.status == 429 or response.status == 403:  # Rate limited or blocked
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
    
    async def search_facebook_marketplace(self, keyword: str, sort: str = "price_low_to_high", max_pages: int = 2) -> List[FacebookListing]:
        """
        Search Facebook Marketplace for a keyword with sorting options.
        
        Args:
            keyword (str): Keyword to search for
            sort (str): Sorting option - "price_low_to_high", "price_high_to_low", "recent", "relevant"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[FacebookListing]: List of found listings
        """
        logger.info(f"Searching Facebook Marketplace for '{keyword}' with sort={sort}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "price_low_to_high": "price_ascend",
            "price_high_to_low": "price_descend",
            "recent": "creation_time_descend",
            "relevant": "best_match"
        }.get(sort, "price_ascend")
        
        encoded_keyword = quote_plus(keyword)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Calculate offset (25 items per page)
            offset = (page - 1) * 25
            
            # Construct URL for the search
            # Note: Facebook Marketplace search URLs can be complex and may change over time
            base_url = "https://www.facebook.com/marketplace/search"
            params = {
                "query": keyword,
                "sortBy": sort_param,
                "exact": "false",
                "latitude": self.location["latitude"],
                "longitude": self.location["longitude"],
                "radius": self.location["radius"],
                "daysSinceListed": "all",
                "offset": offset
            }
            url = f"{base_url}?{urlencode(params)}"
            
            logger.info(f"Fetching page {page} for keyword '{keyword}'")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_facebook_search_results(html)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page} for keyword '{keyword}'")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page} for keyword '{keyword}'")
            
            # If we have fewer listings than expected, we might have reached the end
            if len(page_listings) < 24:  # FB typically shows ~24-25 items per page
                break
        
        logger.info(f"Total of {len(listings)} listings found for keyword '{keyword}'")
        return listings
    
    def _parse_facebook_search_results(self, html: str) -> List[FacebookListing]:
        """
        Parse Facebook Marketplace search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            
        Returns:
            List[FacebookListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all search result items
        # Note: Facebook's HTML structure can change frequently, so these selectors may need updating
        result_elements = soup.select('div[data-testid="marketplace_search_feed_result"], a[role="link"][href*="/marketplace/item/"]')
        
        # Alternative way to find listings - look for JSON data in scripts
        json_data = self._extract_json_data(html)
        if json_data and len(result_elements) == 0:
            # Parse JSON data to get listings
            return self._parse_json_listings(json_data)
        
        for element in result_elements:
            try:
                # Extract listing ID
                listing_id = ""
                link = ""
                if 'href' in element.attrs:
                    link = element['href']
                    if not link.startswith('http'):
                        link = f"https://www.facebook.com{link}"
                    
                    # Extract listing ID
                    id_match = re.search(r'/item/(\d+)', link)
                    if id_match:
                        listing_id = id_match.group(1)
                else:
                    link_elem = element.select_one('a[href*="/marketplace/item/"]')
                    if link_elem and 'href' in link_elem.attrs:
                        link = link_elem['href']
                        if not link.startswith('http'):
                            link = f"https://www.facebook.com{link}"
                        
                        id_match = re.search(r'/item/(\d+)', link)
                        if id_match:
                            listing_id = id_match.group(1)
                
                if not listing_id or not link:
                    continue
                
                # Extract title
                title_elem = element.select_one('span[dir="auto"], span.a8c37x1j')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Extract price
                price = None
                price_elem = element.select_one('span[dir="auto"]:-soup-contains("$")')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                        except ValueError:
                            continue
                
                if price is None:
                    continue
                
                # Extract image URL
                img_url = ""
                img_elem = element.select_one('img[src*="scontent"]')
                if img_elem and 'src' in img_elem.attrs:
                    img_url = img_elem['src']
                
                # Extract location
                location = None
                location_elem = element.select_one('span[dir="auto"]:-soup-contains("in")')
                if location_elem:
                    location_text = location_elem.text.strip()
                    location_match = re.search(r'in\s+(.+)', location_text)
                    if location_match:
                        location = location_match.group(1).strip()
                
                # Extract condition (when available)
                condition = "Used"  # Default assumption for Facebook Marketplace
                condition_elem = element.select_one('span:-soup-contains("New"), span:-soup-contains("Used"), span:-soup-contains("Like New"), span:-soup-contains("Good"), span:-soup-contains("Fair")')
                if condition_elem:
                    condition = condition_elem.text.strip()
                
                # Create listing object
                listing = FacebookListing(
                    title=title,
                    price=price,
                    link=link,
                    image_url=img_url,
                    condition=condition,
                    location=location,
                    seller_name=None,  # Typically found on product page
                    posting_date=None,  # Typically found on product page
                    description=None,   # Typically found on product page
                    listing_id=listing_id
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing Facebook listing: {str(e)}")
                continue
        
        return listings
    
    def _extract_json_data(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from Facebook Marketplace HTML.
        
        Args:
            html (str): HTML content
            
        Returns:
            Optional[Dict[str, Any]]: Extracted JSON data or None
        """
        # Look for marketplace data in scripts
        data_regex = r'marketplace_search_feed_items":\s*(\[.+?\]),\s*"'
        match = re.search(data_regex, html)
        
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON data from HTML")
        
        return None
    
    def _parse_json_listings(self, json_data: List[Dict[str, Any]]) -> List[FacebookListing]:
        """
        Parse Facebook Marketplace listings from JSON data.
        
        Args:
            json_data (List[Dict[str, Any]]): JSON data containing listings
            
        Returns:
            List[FacebookListing]: Parsed listings
        """
        listings = []
        
        for item in json_data:
            try:
                # Skip non-marketplace items
                if 'marketplace_listing' not in item:
                    continue
                
                listing_data = item.get('marketplace_listing', {})
                
                # Extract listing ID
                listing_id = listing_data.get('id', '')
                if not listing_id:
                    continue
                
                # Extract title
                title = listing_data.get('marketplace_listing_title', '')
                if not title:
                    continue
                
                # Extract price
                price_data = listing_data.get('price_amount', {})
                formatted_price = price_data.get('formatted', '')
                price_match = re.search(r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', formatted_price)
                
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        continue
                else:
                    continue
                
                # Extract link
                link = f"https://www.facebook.com/marketplace/item/{listing_id}"
                
                # Extract image URL
                image_url = ""
                images = listing_data.get('primary_listing_photo', {}).get('image', {}).get('uri', '')
                if images:
                    image_url = images
                
                # Extract location
                location = None
                location_data = listing_data.get('location_text', {}).get('text', '')
                if location_data:
                    location = location_data
                
                # Extract condition
                condition = "Used"  # Default
                condition_data = listing_data.get('condition', {}).get('text', '')
                if condition_data:
                    condition = condition_data
                
                # Extract shipping info
                shipping_available = False
                shipping_info = listing_data.get('shipping_info', {})
                if shipping_info:
                    shipping_available = True
                
                # Create listing object
                listing = FacebookListing(
                    title=title,
                    price=price,
                    link=link,
                    image_url=image_url,
                    condition=condition,
                    location=location,
                    seller_name=None,
                    posting_date=None,
                    description=None,
                    listing_id=listing_id,
                    shipping_available=shipping_available
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing Facebook JSON listing: {str(e)}")
                continue
        
        return listings
    
    async def get_listing_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific listing.
        
        Args:
            listing_url (str): Facebook Marketplace listing URL
            
        Returns:
            Optional[Dict[str, Any]]: Listing details, or None if not found
        """
        html = await self.fetch_page(listing_url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('h1[dir="auto"], span.d2edcug0')
        if title_elem:
            details['title'] = title_elem.text.strip()
        
        # Extract price
        price_elem = soup.select_one('span[dir="auto"]:-soup-contains("$"), span.d2edcug0:-soup-contains("$")')
        if price_elem:
            price_text = price_elem.text.strip()
            price_match = re.search(r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
            if price_match:
                try:
                    details['price'] = float(price_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract condition
        condition_elem = soup.select_one('div:-soup-contains("Condition"), span:-soup-contains("Condition")')
        if condition_elem:
            # Look for the value after "Condition"
            next_elem = condition_elem.find_next('span')
            if next_elem:
                details['condition'] = next_elem.text.strip()
        
        # Extract description
        description_elem = soup.select_one('div[dir="auto"]:-soup-contains("Description"), span[dir="auto"]:-soup-contains("Description")')
        if description_elem:
            # Look for the description text after the label
            next_elem = description_elem.find_next('div[dir="auto"], span[dir="auto"]')
            if next_elem:
                details['description'] = next_elem.text.strip()
        
        # Extract location
        location_elem = soup.select_one('div:-soup-contains("Location"), span:-soup-contains("Location")')
        if location_elem:
            # Look for the value after "Location"
            next_elem = location_elem.find_next('span')
            if next_elem:
                details['location'] = next_elem.text.strip()
        
        # Extract seller information
        seller_elem = soup.select_one('a[href*="/user/"]')
        if seller_elem:
            details['seller_name'] = seller_elem.text.strip()
            details['seller_profile'] = seller_elem['href']
        
        # Extract posting date
        date_elem = soup.select_one('span:-soup-contains("Listed"), span:-soup-contains("Posted")')
        if date_elem:
            date_text = date_elem.text.strip()
            date_match = re.search(r'(?:Listed|Posted)\s+(\d+\s+\w+\s+ago|yesterday|today|\w+\s+\d+(?:,\s+\d+)?)', date_text, re.IGNORECASE)
            if date_match:
                details['posting_date'] = date_match.group(1)
        
        # Extract category
        category_elem = soup.select_one('a[href*="/category/"]')
        if category_elem:
            details['category'] = category_elem.text.strip()
        
        # Extract images
        image_elems = soup.select('img[src*="scontent"]')
        image_urls = []
        for img in image_elems:
            if 'src' in img.attrs:
                image_urls.append(img['src'])
        
        if image_urls:
            details['image_urls'] = image_urls
        
        # Look for shipping information
        shipping_elem = soup.select_one('span:-soup-contains("Shipping"), span:-soup-contains("Delivery")')
        if shipping_elem:
            details['shipping_available'] = True
        else:
            details['shipping_available'] = False
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search Facebook Marketplace for products in a specific subcategory by generating keywords.
        
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
        pages_per_keyword = min(3, (max_listings_per_keyword + 24) // 25)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self.search_facebook_marketplace(
                    keyword, 
                    sort="price_low_to_high", 
                    max_pages=pages_per_keyword
                )
                
                # If we need more, search for recently listed items (for selling)
                recent_listings = await self.search_facebook_marketplace(
                    keyword, 
                    sort="recent", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in recent_listings])
                
                logger.info(f"Found {len(low_priced) + len(recent_listings)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching Facebook for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_facebook_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run Facebook Marketplace search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = FacebookScraper(use_proxy=False, delay_between_requests=2.0)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching Facebook Marketplace for subcategory: {subcategory}")
                listings = await scraper.search_subcategory(subcategory)
                
                # Add subcategory to each listing
                for listing in listings:
                    if 'subcategory' not in listing or not listing['subcategory']:
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
    async def test_facebook_scraper():
        subcategories = ["Headphones", "Mechanical Keyboards"]
        results = await run_facebook_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
            if result.get('location'):
                print(f"Location: {result['location']}")
            print(f"Condition: {result['condition']}")
    
    # Run the test
    asyncio.run(test_facebook_scraper())

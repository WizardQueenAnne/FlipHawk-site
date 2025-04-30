"""
TCGPlayer marketplace scraper for FlipHawk arbitrage system.
This module handles scraping TCGPlayer for trading card products based on keywords from the subcategories.
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
logger = logging.getLogger('tcgplayer_scraper')

@dataclass
class TCGPlayerListing:
    """Class to store TCGPlayer product listing information."""
    title: str
    price: float
    market_price: Optional[float]
    link: str
    image_url: str
    condition: str
    set_name: Optional[str]
    rarity: Optional[str]
    seller: Optional[str]
    seller_rating: Optional[float]
    shipping_cost: float = 0.0
    free_shipping: bool = False
    in_stock: bool = True
    quantity_available: Optional[int] = None
    language: str = "English"
    source: str = "TCGPlayer"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the listing to a dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'market_price': self.market_price,
            'link': self.link,
            'image_url': self.image_url,
            'condition': self.condition,
            'set_name': self.set_name,
            'rarity': self.rarity,
            'seller': self.seller,
            'seller_rating': self.seller_rating,
            'shipping_cost': self.shipping_cost,
            'free_shipping': self.free_shipping,
            'in_stock': self.in_stock,
            'quantity_available': self.quantity_available,
            'language': self.language,
            'source': self.source,
            'normalized_title': self.normalize_title()
        }
    
    def normalize_title(self) -> str:
        """Normalize the title for comparison with other listings."""
        # Convert to lowercase
        title = self.title.lower()
        
        # Remove non-alphanumeric characters except spaces
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # For TCG cards, specifically extract card name, set, and condition
        card_parts = []
        
        # Extract card name (likely first part of title)
        if ' - ' in title:
            card_name = title.split(' - ')[0].strip()
            card_parts.append(card_name)
        else:
            card_parts.append(title)
        
        # Add set name if available
        if self.set_name:
            card_parts.append(self.set_name.lower())
        
        # Add condition
        if self.condition:
            card_parts.append(self.condition.lower())
        
        # Add rarity if available
        if self.rarity:
            card_parts.append(self.rarity.lower())
        
        # Combine all parts
        normalized = ' '.join(card_parts)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized


class TCGPlayerScraper:
    """Class for scraping TCGPlayer product listings."""
    
    def __init__(self, use_proxy=False, max_retries=3, delay_between_requests=2.0):
        """
        Initialize the TCGPlayer scraper.
        
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
            'Referer': 'https://www.tcgplayer.com/',
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
        
        # Common TCG games supported by TCGPlayer
        self.tcg_games = {
            "Pokémon": "pokemon",
            "Magic: The Gathering": "magic",
            "Yu-Gi-Oh": "yugioh",
            "Flesh and Blood": "flesh-and-blood",
            "Dragon Ball Super": "dragon-ball-super",
            "MetaZoo": "metazoo",
            "Digimon": "digimon",
            "One Piece": "one-piece",
            "Final Fantasy": "final-fantasy",
            "Star Wars: Unlimited": "star-wars-unlimited"
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
    
    async def search_tcgplayer(self, keyword: str, game: str = "pokemon", sort: str = "price_asc", max_pages: int = 2) -> List[TCGPlayerListing]:
        """
        Search TCGPlayer for a keyword with sorting options and game filtering.
        
        Args:
            keyword (str): Keyword to search for
            game (str): TCG game to search within (pokemon, magic, yugioh, etc.)
            sort (str): Sorting option - "price_asc", "price_desc", "relevance", "release_date"
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            List[TCGPlayerListing]: List of found listings
        """
        logger.info(f"Searching TCGPlayer for '{keyword}' in {game} with sort={sort}")
        
        # Prepare sort parameter for URL
        sort_param = {
            "price_asc": "price_asc",
            "price_desc": "price_desc",
            "relevance": "relevant",
            "release_date": "date_desc"
        }.get(sort, "price_asc")
        
        encoded_keyword = quote_plus(keyword)
        encoded_game = quote_plus(game)
        listings = []
        
        for page in range(1, max_pages + 1):
            # Construct URL for the search
            url = f"https://www.tcgplayer.com/search/all/product?q={encoded_keyword}&productLineName={encoded_game}&productTypeId=&view=grid&page={page}&sort={sort_param}"
            
            logger.info(f"Fetching page {page} for keyword '{keyword}' in {game}")
            html = await self.fetch_page(url)
            
            if not html:
                logger.warning(f"No HTML returned for page {page} of keyword '{keyword}'")
                break
            
            # Parse the HTML and extract listings
            page_listings = self._parse_tcgplayer_search_results(html, game)
            
            if not page_listings:
                logger.warning(f"No listings found on page {page} for keyword '{keyword}'")
                break
            
            listings.extend(page_listings)
            logger.info(f"Found {len(page_listings)} listings on page {page} for keyword '{keyword}'")
            
            # If we have fewer listings than expected, we might have reached the end
            if len(page_listings) < 24:  # TCGPlayer typically shows 24 items per page
                break
        
        logger.info(f"Total of {len(listings)} listings found for keyword '{keyword}'")
        return listings
    
    def _parse_tcgplayer_search_results(self, html: str, game: str) -> List[TCGPlayerListing]:
        """
        Parse TCGPlayer search results HTML.
        
        Args:
            html (str): HTML content of the search results page
            game (str): The TCG game being searched (used for context in parsing)
            
        Returns:
            List[TCGPlayerListing]: List of parsed product listings
        """
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Find all search result items
        result_elements = soup.select('.search-result')
        
        for element in result_elements:
            try:
                # Extract title
                title_elem = element.select_one('.search-result__title')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                if not title:
                    continue
                
                # Extract link
                link = None
                link_elem = element.select_one('a.search-result__link')
                if link_elem and 'href' in link_elem.attrs:
                    link = f"https://www.tcgplayer.com{link_elem['href']}"
                
                if not link:
                    continue
                
                # Extract price
                price = None
                price_elem = element.select_one('.search-result__price')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'\$(\d+\.\d+)', price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1))
                        except ValueError:
                            continue
                
                if price is None:
                    continue
                
                # Extract market price if available
                market_price = None
                market_elem = element.select_one('.search-result__market-price')
                if market_elem:
                    market_text = market_elem.text.strip()
                    market_match = re.search(r'\$(\d+\.\d+)', market_text)
                    if market_match:
                        try:
                            market_price = float(market_match.group(1))
                        except ValueError:
                            pass
                
                # Extract image URL
                img_url = ""
                img_elem = element.select_one('.search-result__image img')
                if img_elem and 'src' in img_elem.attrs:
                    img_url = img_elem['src']
                elif img_elem and 'data-src' in img_elem.attrs:
                    img_url = img_elem['data-src']
                
                # Extract set name
                set_name = None
                set_elem = element.select_one('.search-result__set')
                if set_elem:
                    set_name = set_elem.text.strip()
                
                # Extract rarity
                rarity = None
                rarity_elem = element.select_one('.search-result__rarity')
                if rarity_elem:
                    rarity = rarity_elem.text.strip()
                
                # Extract condition
                condition = "Near Mint"  # Default
                condition_elem = element.select_one('.search-result__condition')
                if condition_elem:
                    condition = condition_elem.text.strip()
                
                # Create listing object
                listing = TCGPlayerListing(
                    title=title,
                    price=price,
                    market_price=market_price,
                    link=link,
                    image_url=img_url,
                    condition=condition,
                    set_name=set_name,
                    rarity=rarity,
                    seller=None,  # TCGPlayer typically shows seller info on product page
                    seller_rating=None
                )
                
                listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error parsing TCGPlayer listing: {str(e)}")
                continue
        
        return listings
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product.
        
        Args:
            product_url (str): TCGPlayer product URL
            
        Returns:
            Optional[Dict[str, Any]]: Product details, or None if not found
        """
        html = await self.fetch_page(product_url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Extract title
        title_elem = soup.select_one('.product-details__name')
        if title_elem:
            details['title'] = title_elem.text.strip()
        
        # Extract set
        set_elem = soup.select_one('.product-details__set')
        if set_elem:
            details['set_name'] = set_elem.text.strip()
        
        # Extract rarity
        rarity_elem = soup.select_one('.product-details__rarity')
        if rarity_elem:
            details['rarity'] = rarity_elem.text.strip()
        
        # Extract market price
        market_elem = soup.select_one('.price-point__market-price')
        if market_elem:
            market_text = market_elem.text.strip()
            market_match = re.search(r'\$(\d+\.\d+)', market_text)
            if market_match:
                try:
                    details['market_price'] = float(market_match.group(1))
                except ValueError:
                    pass
        
        # Extract listings
        listings = []
        listing_elems = soup.select('.product-listing')
        for elem in listing_elems:
            listing = {}
            
            # Price
            price_elem = elem.select_one('.product-listing__price')
            if price_elem:
                price_text = price_elem.text.strip()
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if price_match:
                    try:
                        listing['price'] = float(price_match.group(1))
                    except ValueError:
                        continue
            
            # Seller
            seller_elem = elem.select_one('.seller-info__name')
            if seller_elem:
                listing['seller'] = seller_elem.text.strip()
            
            # Seller rating
            rating_elem = elem.select_one('.seller-info__feedback-rating')
            if rating_elem:
                rating_text = rating_elem.text.strip()
                rating_match = re.search(r'([\d.]+)%', rating_text)
                if rating_match:
                    try:
                        listing['seller_rating'] = float(rating_match.group(1))
                    except ValueError:
                        pass
            
            # Condition
            condition_elem = elem.select_one('.condition-select__current-condition')
            if condition_elem:
                listing['condition'] = condition_elem.text.strip()
            
            # Quantity
            quantity_elem = elem.select_one('.product-listing__quantity-available')
            if quantity_elem:
                quantity_text = quantity_elem.text.strip()
                quantity_match = re.search(r'(\d+)', quantity_text)
                if quantity_match:
                    try:
                        listing['quantity_available'] = int(quantity_match.group(1))
                    except ValueError:
                        pass
            
            # Shipping
            shipping_elem = elem.select_one('.product-listing__shipping')
            if shipping_elem:
                shipping_text = shipping_elem.text.strip().lower()
                if 'free shipping' in shipping_text:
                    listing['free_shipping'] = True
                    listing['shipping_cost'] = 0.0
                else:
                    shipping_match = re.search(r'\$(\d+\.\d+)', shipping_text)
                    if shipping_match:
                        try:
                            listing['shipping_cost'] = float(shipping_match.group(1))
                            listing['free_shipping'] = False
                        except ValueError:
                            pass
            
            listings.append(listing)
        
        if listings:
            details['listings'] = listings
        
        # Extract card details
        card_details = {}
        detail_rows = soup.select('.product-details__table-row')
        for row in detail_rows:
            label_elem = row.select_one('.product-details__table-label')
            value_elem = row.select_one('.product-details__table-value')
            if label_elem and value_elem:
                label = label_elem.text.strip()
                value = value_elem.text.strip()
                if label and value:
                    card_details[label] = value
        
        if card_details:
            details['card_details'] = card_details
        
        # Extract image
        image_elem = soup.select_one('.image-fader__image')
        if image_elem and 'src' in image_elem.attrs:
            details['image_url'] = image_elem['src']
        
        return details
    
    async def search_subcategory(self, subcategory: str, max_keywords: int = 5, max_listings_per_keyword: int = 20) -> List[Dict[str, Any]]:
        """
        Search TCGPlayer for products in a specific subcategory by generating keywords.
        
        Args:
            subcategory (str): Subcategory to search for
            max_keywords (int): Maximum number of keywords to use from the subcategory
            max_listings_per_keyword (int): Maximum number of listings to fetch per keyword
            
        Returns:
            List[Dict[str, Any]]: List of found products
        """
        # Determine which TCG game this subcategory belongs to
        game = "pokemon"  # Default to Pokemon
        for game_name, game_code in self.tcg_games.items():
            if subcategory == game_name:
                game = game_code
                break
        
        # Generate keywords for the subcategory
        keywords = generate_keywords(subcategory, include_variations=True, max_keywords=max_keywords)
        
        if not keywords:
            logger.warning(f"No keywords found for subcategory: {subcategory}")
            return []
        
        # Calculate appropriate page depth based on max_listings_per_keyword
        pages_per_keyword = min(3, (max_listings_per_keyword + 23) // 24)
        
        all_listings = []
        
        for keyword in keywords:
            try:
                # Search for low-priced items first (for buying)
                low_priced = await self.search_tcgplayer(
                    keyword, 
                    game=game,
                    sort="price_asc", 
                    max_pages=pages_per_keyword
                )
                
                # If we need more, search for high-priced items (for selling)
                high_priced = await self.search_tcgplayer(
                    keyword, 
                    game=game,
                    sort="price_desc", 
                    max_pages=pages_per_keyword
                )
                
                all_listings.extend([listing.to_dict() for listing in low_priced])
                all_listings.extend([listing.to_dict() for listing in high_priced])
                
                logger.info(f"Found {len(low_priced) + len(high_priced)} total listings for keyword: {keyword}")
                
                # Avoid hitting rate limits
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error searching TCGPlayer for keyword '{keyword}': {str(e)}")
                continue
        
        logger.info(f"Found {len(all_listings)} total listings for subcategory: {subcategory}")
        return all_listings

async def run_tcgplayer_search(subcategories: List[str]) -> List[Dict[str, Any]]:
    """
    Run TCGPlayer search for multiple subcategories.
    
    Args:
        subcategories (List[str]): List of subcategories to search for
        
    Returns:
        List[Dict[str, Any]]: Combined list of found products
    """
    scraper = TCGPlayerScraper(use_proxy=False, delay_between_requests=2.0)
    
    try:
        all_listings = []
        
        for subcategory in subcategories:
            try:
                logger.info(f"Searching TCGPlayer for subcategory: {subcategory}")
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
    async def test_tcgplayer_scraper():
        subcategories = ["Pokémon", "Magic: The Gathering"]
        results = await run_tcgplayer_search(subcategories)
        print(f"Found {len(results)} products")
        
        # Print sample results
        for i, result in enumerate(results[:5]):
            print(f"\nResult #{i+1}:")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']}")
            print(f"Link: {result['link']}")
            print(f"Set: {result.get('set_name', 'N/A')}")
            print(f"Rarity: {result.get('rarity', 'N/A')}")
            print(f"Condition: {result.get('condition', 'N/A')}")
    
    # Run the test
    asyncio.run(test_tcgplayer_scraper())

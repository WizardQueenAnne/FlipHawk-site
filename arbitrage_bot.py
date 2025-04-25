# arbitrage_bot.py - Enhanced FlipHawk Scraper

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import json
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('arbitrage_bot')

@dataclass
class Listing:
    title: str
    price: float
    link: str
    image_url: str
    free_shipping: bool
    normalized_title: str
    source: str
    condition: str = "New"
    seller_rating: Optional[float] = None
    location: Optional[str] = None
    item_specifics: Dict[str, str] = None
    shipping_cost: float = 0.0
    sold_count: int = 0
    timestamp: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'price': self.price,
            'link': self.link,
            'image_url': self.image_url,
            'free_shipping': self.free_shipping,
            'normalized_title': self.normalized_title,
            'source': self.source,
            'condition': self.condition,
            'seller_rating': self.seller_rating,
            'location': self.location,
            'item_specifics': self.item_specifics,
            'shipping_cost': self.shipping_cost,
            'sold_count': self.sold_count,
            'timestamp': self.timestamp or time.strftime('%Y-%m-%d %H:%M:%S')
        }

class Scraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.proxy_pool = self._load_proxies()
        self.rate_limit_delay = 1.0
        self.max_retries = 3
        
    def _load_proxies(self) -> List[str]:
        """Load proxy list from environment or config file."""
        # In production, load from environment or external service
        return []
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page(self, url: str, retries: int = 0) -> Optional[str]:
        """Fetch page with retry logic and error handling."""
        if retries >= self.max_retries:
            logger.error(f"Max retries reached for URL: {url}")
            return None
        
        try:
            session = await self.get_session()
            proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
            
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:  # Rate limited
                    delay = (2 ** retries) * self.rate_limit_delay
                    logger.warning(f"Rate limited. Waiting {delay} seconds...")
                    await asyncio.sleep(delay)
                    return await self.fetch_page(url, retries + 1)
                else:
                    logger.error(f"HTTP {response.status} for URL: {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            if retries < self.max_retries:
                await asyncio.sleep(self.rate_limit_delay)
                return await self.fetch_page(url, retries + 1)
            return None
    
    async def search_ebay(self, keyword: str, sort: str = "price_asc", min_price: float = None, max_price: float = None) -> List[Listing]:
        """Search eBay with additional filters and parameters."""
        encoded_keyword = quote_plus(keyword)
        sort_param = "15" if sort == "price_asc" else "16"
        
        url_parts = [
            f"https://www.ebay.com/sch/i.html?_nkw={encoded_keyword}",
            f"_sop={sort_param}",
            "LH_BIN=1",  # Buy It Now only
            "LH_ItemCondition=1000|1500|2000|2500|3000",  # New and Like New conditions
            "LH_PrefLoc=1"  # US only
        ]
        
        if min_price:
            url_parts.append(f"_udlo={min_price}")
        if max_price:
            url_parts.append(f"_udhi={max_price}")
        
        url = "&".join(url_parts)
        
        html = await self.fetch_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        items = soup.select('li.s-item')
        
        for item in items[:30]:  # Increased limit
            try:
                listing = self._parse_ebay_item(item)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Error parsing eBay item: {str(e)}")
                continue
        
        return listings
    
    def _parse_ebay_item(self, item) -> Optional[Listing]:
        """Parse eBay item with enhanced data extraction."""
        # Skip sponsored items
        if 'srp-river-results-null-search__item' in item.get('class', []):
            return None
        
        # Extract title
        title_elem = item.select_one('.s-item__title')
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        if 'Shop on eBay' in title:
            return None
        
        # Extract price
        price_elem = item.select_one('.s-item__price')
        if not price_elem:
            return None
        
        price_text = price_elem.get_text(strip=True)
        
        # Handle price ranges
        if ' to ' in price_text:
            prices = re.findall(r'[\d,]+\.?\d*', price_text)
            if len(prices) >= 2:
                try:
                    price = (float(prices[0].replace(',', '')) + float(prices[1].replace(',', ''))) / 2
                except:
                    return None
            else:
                return None
        else:
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if not price_match:
                return None
            try:
                price = float(price_match.group(0).replace(',', ''))
            except:
                return None
        
        # Extract link
        link_elem = item.select_one('a.s-item__link')
        if not link_elem:
            return None
        link = link_elem['href'].split('?')[0]
        
        # Extract image
        img_elem = item.select_one('.s-item__image-img')
        img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
        
        # Extract shipping info
        shipping_elem = item.select_one('.s-item__shipping, .s-item__freeXDays')
        shipping_text = shipping_elem.get_text(strip=True) if shipping_elem else ""
        free_shipping = 'Free' in shipping_text
        
        # Extract shipping cost if not free
        shipping_cost = 0.0
        if not free_shipping and shipping_elem:
            shipping_match = re.search(r'\$?([\d.]+)', shipping_text)
            if shipping_match:
                try:
                    shipping_cost = float(shipping_match.group(1))
                except:
                    pass
        
        # Extract condition
        condition_elem = item.select_one('.SECONDARY_INFO')
        condition = condition_elem.get_text(strip=True) if condition_elem else "New"
        
        # Extract location
        location_elem = item.select_one('.s-item__location')
        location = location_elem.get_text(strip=True) if location_elem else None
        
        # Extract sold count
        sold_elem = item.select_one('.s-item__quantitySold')
        sold_count = 0
        if sold_elem:
            sold_match = re.search(r'(\d+)', sold_elem.get_text())
            if sold_match:
                sold_count = int(sold_match.group(1))
        
        return Listing(
            title=title,
            price=price,
            link=link,
            image_url=img_url,
            free_shipping=free_shipping,
            normalized_title=self.normalize_title(title),
            source='eBay',
            condition=condition,
            location=location,
            shipping_cost=shipping_cost,
            sold_count=sold_count
        )
    
    def normalize_title(self, title: str) -> str:
        """Enhanced title normalization with NLP techniques."""
        # Convert to lowercase
        title = title.lower()
        
        # Remove common filler words
        fillers = [
            'brand new', 'new', 'sealed', 'mint', 'condition', 'authentic', 
            'genuine', 'official', 'in box', 'inbox', 'with box', 'unopened', 
            'fast shipping', 'free shipping', 'ships fast', 'lot of', 'set of',
            'excellent', 'great', 'like new', 'oem', 'original', 'factory',
            'bundle', 'rare', 'htf', 'hard to find', 'limited', 'exclusive',
            'complete', '100%', 'perfect', 'amazing', 'clean', 'tested',
            'working', 'fully functional', 'guaranteed', 'warranty',
            'factory sealed', 'brand-new', 'bnib', 'nib', 'mib', 'usa seller',
            'in hand', 'ready to ship', 'same day shipping', 'fast ship'
        ]
        
        for filler in fillers:
            title = title.replace(filler, '')
        
        # Remove special characters and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
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
        
        if models:
            title = ' '.join(models) + ' ' + title
        
        return title

class ArbitrageAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            max_features=5000
        )
        self.model_patterns = [
            r'(?:model|part|sku|item|ref)?\s*(?:#|number|no\.?)?\s*([a-z0-9]{4,})',
            r'[a-z]+\d+[a-z]*\d*',
            r'\d{3,}[a-z]+\d*'
        ]
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity using multiple methods."""
        # Basic sequence matching
        sequence_sim = SequenceMatcher(None, title1, title2).ratio()
        
        # TF-IDF cosine similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([title1, title2])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            cosine_sim = 0.0
        
        # Model number matching
        models1 = set()
        models2 = set()
        
        for pattern in self.model_patterns:
            models1.update(re.findall(pattern, title1))
            models2.update(re.findall(pattern, title2))
        
        model_sim = 0.0
        if models1 and models2:
            model_sim = len(models1.intersection(models2)) / len(models1.union(models2))
        
        # Weighted combination
        weights = {
            'sequence': 0.3,
            'cosine': 0.4,
            'model': 0.3
        }
        
        final_similarity = (
            weights['sequence'] * sequence_sim +

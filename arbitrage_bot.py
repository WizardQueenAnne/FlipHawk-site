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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.proxy_pool = self._load_proxies()
        self.rate_limit_delay = 1.5  # Increased delay
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
            
            # Add random delay to avoid rate limiting
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
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
            "LH_ItemCondition=1000|1500|2000",  # New and Like New conditions only
            "LH_PrefLoc=1",  # US only
            "rt=nc",  # Non-category specific search
            "_ipg=200"  # 200 items per page
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
        
        # Find all search result items
        items = soup.select('li.s-item')
        
        for item in items[:50]:  # Increased limit for better matching
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
        # Skip sponsored items and empty results
        if any(cls in item.get('class', []) for cls in ['srp-river-results-SEARCH_STATUS', 'srp-river-results-null-search__item']):
            return None
        
        # Extract title
        title_elem = item.select_one('.s-item__title')
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        if 'Shop on eBay' in title or title.startswith('Tap'):
            return None
        
        # Extract price
        price_elem = item.select_one('.s-item__price')
        if not price_elem:
            return None
        
        price_text = price_elem.get_text(strip=True)
        
        # Handle price ranges - take the lower price
        if ' to ' in price_text:
            prices = re.findall(r'[\d,]+\.?\d*', price_text)
            if len(prices) >= 2:
                try:
                    price = float(prices[0].replace(',', ''))
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
        link = link_elem['href'].split('?')[0]  # Remove URL parameters
        
        # Extract image
        img_elem = item.select_one('.s-item__image-img')
        img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
        
        # Extract shipping info
        shipping_elem = item.select_one('.s-item__shipping, .s-item__freeXDays, .s-item__logisticsCost')
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
        sold_elem = item.select_one('.s-item__quantitySold, .s-item__hotness')
        sold_count = 0
        if sold_elem:
            sold_match = re.search(r'(\d+)\s*sold', sold_elem.get_text(), re.IGNORECASE)
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
        """Enhanced title normalization with stricter cleaning."""
        # Convert to lowercase
        title = title.lower()
        
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
        """Calculate similarity using multiple methods with stricter matching."""
        # Extract model numbers first
        models1 = set()
        models2 = set()
        
        for pattern in self.model_patterns:
            models1.update(re.findall(pattern, title1))
            models2.update(re.findall(pattern, title2))
        
        # If model numbers don't match at all, return low similarity
        if models1 and models2 and not models1.intersection(models2):
            return 0.3
        
        # Basic sequence matching
        sequence_sim = SequenceMatcher(None, title1, title2).ratio()
        
        # TF-IDF cosine similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([title1, title2])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            cosine_sim = 0.0
        
        # Model number matching
        model_sim = 0.0
        if models1 and models2:
            model_sim = len(models1.intersection(models2)) / len(models1.union(models2))
        
        # Weighted combination with higher threshold
        weights = {
            'sequence': 0.3,
            'cosine': 0.3,
            'model': 0.4  # Increased weight for model matching
        }
        
        final_similarity = (
            weights['sequence'] * sequence_sim +
            weights['cosine'] * cosine_sim +
            weights['model'] * model_sim
        )
        
        return final_similarity
    
    def find_opportunities(self, low_priced: List[Listing], high_priced: List[Listing], 
                           min_profit: float = 15.0, min_profit_percent: float = 25.0) -> List[Dict[str, Any]]:
        """Find arbitrage opportunities with stricter matching criteria."""
        opportunities = []
        
        for low in low_priced:
            for high in high_priced:
                # Skip if comparing the same item (same URL)
                if low.link == high.link:
                    continue
                
                # Calculate similarity with higher threshold
                similarity = self.calculate_similarity(low.normalized_title, high.normalized_title)
                
                if similarity >= 0.85:  # Increased threshold for stricter matching
                    # Calculate profit metrics
                    buy_price = low.price + low.shipping_cost
                    sell_price = high.price
                    profit = sell_price - buy_price
                    profit_percentage = (profit / buy_price) * 100 if buy_price > 0 else 0
                    
                    # Skip if profit is too low
                    if profit < min_profit or profit_percentage < min_profit_percent:
                        continue
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence(
                        low, high, similarity, profit_percentage
                    )
                    
                    # Only include high-confidence matches
                    if confidence >= 75:
                        opportunity = {
                            'title': low.title,
                            'buyPrice': buy_price,
                            'sellPrice': sell_price,
                            'buyLink': low.link,
                            'sellLink': high.link,
                            'profit': profit,
                            'profitPercentage': profit_percentage,
                            'confidence': round(confidence),
                            'similarity': similarity,
                            'buyCondition': low.condition,
                            'sellCondition': high.condition,
                            'buyLocation': low.location,
                            'sellLocation': high.location,
                            'image_url': low.image_url or high.image_url,
                            'sold_count': high.sold_count,
                            'buyShipping': low.shipping_cost,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_confidence(self, low: Listing, high: Listing, similarity: float, profit_percentage: float) -> float:
        """Calculate confidence score with stricter criteria."""
        # Base confidence from similarity
        base_confidence = similarity * 100
        
        # Condition must match exactly for high confidence
        condition_penalty = 0
        if low.condition != high.condition:
            condition_penalty = 15  # Increased penalty
        
        # Bonus for high profit percentage
        profit_bonus = min(5, profit_percentage / 10)
        
        # Bonus for sold count
        sold_bonus = min(5, high.sold_count / 10)
        
        # Penalty for location mismatch
        location_penalty = 0
        if low.location and high.location:
            if low.location != high.location:
                location_penalty = 5
        
        # Calculate final confidence
        confidence = base_confidence - condition_penalty + profit_bonus + sold_bonus - location_penalty
        
        return max(0, min(100, confidence))

class KeywordGenerator:
    def __init__(self):
        self.comprehensive_keywords = self._load_comprehensive_keywords()
    
    def _load_comprehensive_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Load comprehensive keyword database with misspellings and variations."""
        return {
            "Tech": {
                "Headphones": [
                    # Apple AirPods variations
                    "airpods", "airpod", "air pods", "air pod", "apple earbuds", "apple earpods",
                    "airpods pro", "airpods max", "airpods 2", "airpods 3", "airpods pro 2",
                    "airpds", "aripos", "aripods", "apods", "ap pods", "apple airpads",
                    
                    # Beats variations
                    "beats", "beats headphones", "beats solo", "beats studio", "beats pro",
                    "beats studio buds", "beats fit pro", "powerbeats", "powerbeats pro",
                    "beets", "bats headphones", "beatz", "bts headphones",
                    
                    # Bose variations
                    "bose", "bose headphones", "bose quietcomfort", "bose 700", "bose qc",
                    "bose nc", "bose earbuds", "bose soundsport", "bose qc35", "bose qc45",
                    "boss headphones", "boze", "bosee", "quiet comfort",
                    
                    # Sony variations
                    "sony wh", "sony headphones", "sony wf", "sony xm4", "sony xm5",
                    "sony wh-1000xm4", "sony wh-1000xm5", "sony wf-1000xm4",
                    "sonny headphones", "soney", "sony x1000",
                    
                    # General terms and brands
                    "wireless headphones", "bluetooth earbuds", "noise cancelling",
                    "anc headphones", "true wireless", "earphones", "ear buds",
                    "sennheiser", "jabra", "jbl", "marshall", "skullcandy",
                    "samsung buds", "galaxy buds", "pixel buds"
                ],
                
                "Keyboards": [
                    # Mechanical keyboards
                    "mechanical keyboard", "mech keyboard", "gaming keyboard", "rgb keyboard",
                    "cherry mx", "custom keyboard", "hot swap keyboard", "60% keyboard",
                    "65% keyboard", "75% keyboard", "tkl keyboard", "full size keyboard",
                    "mechancial", "mechanicl", "mech kybd", "mechanica keyboard",
                    
                    # Popular brands
                    "logitech keyboard", "corsair keyboard", "razer keyboard", "keychron",
                    "ducky keyboard", "das keyboard", "hyperx keyboard", "steelseries keyboard",
                    "logitec", "corsare", "razor", "steel series", "keycrn",
                    
                    # Specific models
                    "logitech g915", "corsair k70", "razer huntsman", "ducky one 2",
                    "keychron k2", "anne pro", "gmmk pro", "keyboard and mouse combo",
                    "corair k95", "razr black widow", "ducky on2", "anna pro",
                    
                    # Wireless options
                    "wireless keyboard", "bluetooth keyboard", "wireless mechanical",
                    "2.4ghz keyboard", "usb-c keyboard", "multi-device keyboard",
                    "blutooth keyboard", "wi-fi keyboard", "usbc"
                ],
                
                "Graphics Cards": [
                    # NVIDIA cards
                    "rtx 3080", "rtx 3070", "rtx 3060", "rtx 3090", "rtx 4090", "rtx 4080",
                    "geforce rtx", "nvidia gpu", "gtx 1660", "gtx 1080", "gtx 1070",
                    "rtx 3080ti", "rtx 3070ti", "rtx3090", "rtx4090", "nividia",
                    "rtx thirty eighty", "rtx thirty ninety", "rtx forty ninety",
                    
                    # AMD cards
                    "rx 6800", "rx 6900", "rx 6700", "rx 6600", "rx 7900", "radeon gpu",
                    "amd radeon", "rx 580", "rx 570", "rx 5700", "vega 64", "vega 56",
                    "radion", "amd gpu", "rdna 2", "rdna 3", "rx6800xt", "rx6900xt",
                    
                    # General terms
                    "graphics card", "video card", "gpu", "gaming gpu", "mining gpu",
                    "workstation gpu", "professional gpu", "quadro", "firepro",
                    "grphics card", "grfx card", "videoscard", "vga card"
                ],
                
                "CPUs": [
                    # Intel processors
                    "intel i7", "intel i9", "intel i5", "core i7", "core i9", "core i5",
                    "i7-13700k", "i9-13900k", "i7-12700k", "i9-12900k", "lga 1700",
                    "intel cpu", "intel processor", "pentium", "celeron",
                    "intel eye7", "intl i7", "intell", "core eye 7",
                    
                    # AMD processors
                    "ryzen 7", "ryzen 9", "ryzen 5", "amd cpu", "amd processor",
                    "ryzen 7800x3d", "ryzen 7950x", "ryzen 5800x3d", "ryzen threadripper",
                    "am4 cpu", "am5 cpu", "ryzen 5000", "ryzen 7000",
                    "ryzan", "rizen", "amd ryzn", "ryen", "thred ripper",
                    
                    # General terms
                    "processor", "cpu", "desktop cpu", "laptop cpu", "gaming cpu",
                    "workstation cpu", "server cpu", "processer", "proccessor"
                ],
                
                "Laptops": [
                    # MacBooks
                    "macbook", "macbook pro", "macbook air", "mac book", "macbookpro",
                    "m1 macbook", "m2 macbook", "m3 macbook", "apple laptop",
                    "mac pro", "mac air", "mackbook", "macbok", "mac book pro",
                    
                    # Gaming laptops
                    "gaming laptop", "rog laptop", "legion laptop", "msi laptop",
                    "alienware laptop", "razer blade", "asus rog", "predator laptop",
                    "gamming laptop", "rogen laptop", "alisware", "razr blade",
                    
                    # Business laptops
                    "thinkpad", "dell xps", "hp elitebook", "surface laptop",
                    "business laptop", "ultrabook", "2-in-1 laptop", "chromebook",
                    "think pad", "dell xbs", "hp elite", "surface book",
                    
                    # General terms
                    "laptop computer", "notebook", "gaming notebook", "laptop pc",
                    "labtop", "lap top", "note book", "leptop"
                ],
                
                "Monitors": [
                    # Gaming monitors
                    "gaming monitor", "144hz monitor", "240hz monitor", "360hz monitor",
                    "4k monitor", "1440p monitor", "ultrawide monitor", "curved monitor",
                    "ips monitor", "va monitor", "tn monitor", "oled monitor",
                    "gamign monitor", "144 hz", "240 hz", "fourk monitor",
                    
                    # Brands and models
                    "lg ultragear", "samsung odyssey", "asus rog", "acer predator",
                    "dell monitor", "hp monitor", "benq monitor", "viewsonic",
                    "lg ultra gear", "samsuung", "rog swift", "predater monitor",
                    
                    # Professional monitors
                    "4k professional", "color accurate monitor", "design monitor",
                    "video editing monitor", "content creation monitor", "srgb monitor",
                    "color acurate", "profesional monitor", "adobe rgb"
                ],
                
                "SSDs": [
                    # Popular brands
                    "samsung evo", "crucial mx500", "western digital ssd", "wd black",
                    "sandisk ssd", "kingston ssd", "nvme ssd",

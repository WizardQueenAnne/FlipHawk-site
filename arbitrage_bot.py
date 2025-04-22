"""
FlipHawk Arbitrage Bot - Optimized
A real-time scraper that finds arbitrage opportunities across marketplaces.
This version focuses on speed, accuracy, and comprehensive keyword generation.
"""

import asyncio
import aiohttp
import re
import time
import logging
import random
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from urllib.parse import quote_plus

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('arbitrage_bot')

# Constants
MAX_CONCURRENT_REQUESTS = 25  # Higher for faster scraping
REQUEST_TIMEOUT = 8  # Shorter timeout for speed
MIN_PROFIT_PERCENTAGE = 20  # Minimum ROI 
MIN_PROFIT_DOLLARS = 15  # Minimum absolute profit
MAX_RESULTS_PER_SUBCATEGORY = 5  # Keep only the best opportunities
SIMILARITY_THRESHOLD = 0.78  # Threshold for considering items as the same 

# Categories and subcategories
CATEGORIES = {
    "Tech": ["Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops", "Monitors", "SSDs", "Routers", "Vintage Tech"],
    "Collectibles": ["Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards", "Comic Books", "Action Figures", "LEGO Sets"],
    "Vintage Clothing": ["Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets", "Designer Brands", "Carhartt", "Patagonia"],
    "Antiques": ["Coins", "Watches", "Cameras", "Typewriters", "Vinyl Records", "Vintage Tools", "Old Maps", "Antique Toys"],
    "Gaming": ["Consoles", "Game Controllers", "Rare Games", "Arcade Machines", "Handhelds", "Gaming Headsets", "VR Gear"],
    "Music Gear": ["Electric Guitars", "Guitar Pedals", "Synthesizers", "Vintage Amps", "Microphones", "DJ Equipment"],
    "Tools & DIY": ["Power Tools", "Hand Tools", "Welding Equipment", "Toolboxes", "Measuring Devices", "Woodworking Tools"],
    "Outdoors & Sports": ["Bikes", "Skateboards", "Scooters", "Camping Gear", "Hiking Gear", "Fishing Gear", "Snowboards"]
}

# User agents for rotation to avoid rate limiting
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

# Advanced keyword generators
def generate_keywords(subcategory):
    """Generate extensive keywords for the subcategory including typos, variations, etc."""
    keywords = [subcategory]  # Start with the exact subcategory name
    
    # Dictionary of predefined keywords for each subcategory
    subcategory_keywords = {
        "Magic: The Gathering": [
            "MTG", "Magic The Gathering", "Magic cards", "MtG cards", 
            "Magic booster", "MTG singles", "Magic: The Gathering cards",
            "MTG rare", "Magic foil", "Commander deck", "Magic mythic",
            "MTG collection", "Magic TCG", "Magic sealed", "Magic booster box",
            "Magic standard", "Magic modern", "Magic commander", "Magic vintage",
            "Magic legacy", "Magic collector", "Magic draft", "Magic: TG",
            # Common typos and misspellings
            "Majic the Gathering", "Magic the Gathring", "Magik the Gathering",
            "Magic teh Gathering", "MGT", "MTG crads", "Mtg cads", "Majic cards",
            "Magictg", "Magci", "Maigc", "Mgaic", "MTG lot", "Majic the gathring"
        ],
        "Pokémon": [
            "Pokemon", "Pokemon cards", "Pokemon TCG", "Pokemon Trading Card Game",
            "Pokemon packs", "Pokemon box", "Pokemon booster", "Pokemon rare",
            "Pokemon collection", "Pokemon singles", "Pokemon sealed", "Pokemon PSA",
            "Pokemon graded", "Pokemon lot", "Pokemon set", "Pokemon vintage",
            "Pokemon WOTC", "Pokemon ex", "Pokemon gx", "Pokemon v", "Pokemon vmax",
            # Specific card names that are popular
            "Charizard", "Pikachu", "Blastoise", "Venusaur", "Mewtwo", "Lugia",
            # Common typos and misspellings
            "Pokmon", "Pokeemon", "Pokemn", "Pokeman", "Pokemin", "Poekmon", 
            "Pokéman", "Pokmen", "Pokmeon", "Pokmn", "Pokmon cards", "Pokmen cards"
        ],
        "Yu-Gi-Oh": [
            "Yugioh", "Yu-Gi-Oh", "Yu Gi Oh", "YGO", "Yugioh cards", "Yu-Gi-Oh cards",
            "Yugioh rare", "YGO collection", "Yugioh booster", "Yu-Gi-Oh deck",
            "Yugioh singles", "Yugioh lot", "Yu-Gi-Oh collection", "Yugioh set", 
            "Yugioh sealed", "Yugioh 1st edition", "Yugioh unlimited", "Yugioh PSA",
            # Common typos and misspellings
            "Yugio", "Yugi-oh", "Yugiho", "Yu gi ho", "Yugi oh", "Yugi-ho", "Yu-gi-ho",
            "Yugiooh", "Yuigoh", "YuGiOh", "Yu-Gi-Yo", "Yu-Gi-o", "Yugih", "Yugio cards"
        ],
        "Headphones": [
            "headphones", "wireless headphones", "bluetooth headphones", "noise cancelling headphones",
            "over ear headphones", "on ear headphones", "earbuds", "wireless earbuds", "in-ear headphones",
            "studio headphones", "audiophile headphones", "high-end headphones", "gaming headset",
            "Sony headphones", "Bose headphones", "Sennheiser headphones", "AKG headphones", 
            "Audio-Technica headphones", "Beyerdynamic headphones", "JBL headphones", "Beats headphones",
            # Models
            "WH-1000XM4", "WH-1000XM5", "QC45", "QC35", "HD660S", "HD650", "HD600", "AirPods Pro",
            # Common typos
            "headphons", "heaphones", "hedphones", "hedphnes", "eadphones", "headfones", "haedphones"
        ],
        "Keyboards": [
            "keyboard", "mechanical keyboard", "gaming keyboard", "wireless keyboard", 
            "bluetooth keyboard", "60% keyboard", "TKL keyboard", "full-size keyboard",
            "ortholinear keyboard", "split keyboard", "custom keyboard", "keyboard kit",
            "Cherry MX", "Gateron", "Kailh", "Zealio", "Topre", "hot swap keyboard",
            "PBT keycaps", "keyboard foam", "keyboard lube", "keyboard switches",
            # Brands
            "Ducky keyboard", "Logitech keyboard", "Razer keyboard", "Corsair keyboard",
            "Keychron", "GMMK", "Drop keyboard", "KBDfans", "Royal Kludge",
            # Common typos
            "keybaord", "keyborad", "keybord", "keboard", "keyboar", "keyboad", "meachanical"
        ],
        "Jordans": [
            "Air Jordan", "Jordan 1", "Jordan 4", "Jordan 3", "Jordan 11", "Jordan 5",
            "Nike Jordan", "Jordan High", "Jordan Mid", "Jordan Low", "Jordan Retro",
            "Chicago Jordan", "Bred Jordan", "Banned Jordan", "Shadow Jordan", "Royal Jordan",
            "Jordan OG", "Jordan collab", "Jordan Travis Scott", "Jordan Off-White",
            "Jordan Fragment", "Jordan Patent", "Jordan University Blue",
            # Common typos
            "Jordon", "Jourdan", "Jodan", "Jordns", "Jordens", "Jorden", "Jordn",
            "Air Jodan", "Nike Jordon", "Jodens", "Jorden 1"
        ],
        "Graphics Cards": [
            "GPU", "graphics card", "video card", "gaming GPU", "Nvidia GPU", "AMD GPU", 
            "RTX 3090", "RTX 3080", "RTX 3070", "RTX 3060", "RTX 2080", "RTX 2070", 
            "RX 6900", "RX 6800", "RX 6700", "GDDR6", "GDDR6X", "ray tracing GPU",
            "MSI GPU", "ASUS GPU", "EVGA GPU", "Gigabyte GPU", "Founders Edition",
            # Common typos
            "grpahics card", "grphics card", "grafics card", "grahpics card", "graphic card", 
            "video crad", "vidoe card", "graphcis card", "nvidia grapics", "NVidia"
        ],
        "Consoles": [
            "gaming console", "video game console", "game system", "PlayStation", "PS5", "PS4", 
            "PlayStation 5", "PlayStation 4", "Xbox", "Xbox Series X", "Xbox Series S", 
            "Xbox One", "Nintendo Switch", "Switch OLED", "Switch Lite", "Nintendo", 
            "game console", "console bundle", "special edition console", "limited edition console",
            # Common typos
            "Playstation", "Play Station", "PlsyStation", "Platstation", "P55", "PS", 
            "XBox", "X box", "X-Box", "Nintedo", "Nintento", "Swich", "Nitendo", "Swtich"
        ]
        # Add more subcategories as needed
    }
    
    # Add predefined keywords for the subcategory if available
    if subcategory in subcategory_keywords:
        keywords.extend(subcategory_keywords[subcategory])
    else:
        # If not found exactly, try finding partial matches
        for key, values in subcategory_keywords.items():
            if key.lower() in subcategory.lower() or subcategory.lower() in key.lower():
                keywords.extend(values)
                break
    
    # Generate common typos for the subcategory if it's not already in our predefined lists
    if len(keywords) < 5:
        # Simple typo generator for subcategory name
        for i in range(len(subcategory)):
            if i > 0:
                # Swap adjacent characters
                typo = subcategory[:i-1] + subcategory[i] + subcategory[i-1] + subcategory[i+1:]
                keywords.append(typo)
            
            # Remove one character
            if len(subcategory) > 4:  # Only if word is long enough
                typo = subcategory[:i] + subcategory[i+1:]
                keywords.append(typo)
                
        # Add a space in a random position for multi-word subcategories
        words = subcategory.split()
        if len(words) > 1:
            for i, word in enumerate(words):
                if len(word) > 3:
                    mid = len(word) // 2
                    typo_words = words.copy()
                    typo_words[i] = word[:mid] + " " + word[mid:]
                    keywords.append(" ".join(typo_words))
    
    # Remove duplicates and limit to a reasonable number for performance
    unique_keywords = list(dict.fromkeys([k.strip() for k in keywords if k.strip()]))
    return unique_keywords[:20]  # Limit to 20 keywords for performance

def get_random_user_agent():
    """Get a random user agent to avoid detection."""
    return random.choice(USER_AGENTS)

async def fetch_page(session, url, retries=2):
    """Fetch a webpage with retry logic."""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    for attempt in range(retries + 1):
        try:
            async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:  # Too many requests
                    wait_time = (attempt + 1) * 2  # Progressive backoff
                    logger.warning(f"Rate limited - waiting {wait_time}s before retry {attempt+1}/{retries}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.warning(f"Error fetching {url}: Status {response.status} (Attempt {attempt+1}/{retries})")
                    if attempt < retries:
                        await asyncio.sleep(1)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url} (Attempt {attempt+1}/{retries})")
            if attempt < retries:
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Exception fetching {url}: {str(e)} (Attempt {attempt+1}/{retries})")
            if attempt < retries:
                await asyncio.sleep(1)
    
    return None  # Return None if all retries failed

def normalize_title(title):
    """Normalize product title for better comparison."""
    if not title:
        return ""
    
    # Convert to lowercase
    title = title.lower()
    
    # Remove common filler phrases
    fillers = [
        'brand new', 'new', 'sealed', 'mint', 'condition', 'authentic', 
        'genuine', 'official', 'with box', 'in box', 'unopened', 'fast shipping',
        'free shipping', 'ships fast', 'lot of', 'bundle', 'rare', 'hard to find',
        'limited', 'exclusive', 'excellent', 'great', 'like new', 'tested', 'working'
    ]
    
    for filler in fillers:
        title = re.sub(r'\b' + re.escape(filler) + r'\b', '', title)
    
    # Remove special characters and extra spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def extract_model_numbers(title):
    """Extract model numbers from title for better matching."""
    patterns = [
        r'\b[A-Z0-9]{2,4}-[A-Z0-9]{2,6}\b',  # Format: XX-XXXX
        r'\b[A-Z][0-9]{1,4}[A-Z]?\b',        # Format: X###X
        r'\b[A-Z]{1,3}[0-9]{2,5}\b',         # Format: XX###
        r'\b[0-9]{1,2}[A-Z]{1,2}[0-9]{1,4}\b'  # Format: #XX###
    ]
    
    model_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, title.upper())
        model_numbers.extend(matches)
    
    return model_numbers

async def search_ebay_listings(session, keyword, sort="price_asc", max_listings=40):
    """
    Search eBay for listings with the given keyword.
    Optimized for speed and accuracy.
    """
    encoded_keyword = quote_plus(keyword)
    
    # Determine sort parameter
    sort_param = "15" if sort == "price_asc" else "16"  # 15=lowest, 16=highest
    
    # Build URL with advanced search parameters:
    # - Buy It Now only (no auctions)
    # - New and Like New condition
    # - US only (for more accurate shipping costs)
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_keyword}&_sop={sort_param}&LH_BIN=1&_fsrp=1&_sacat=0&LH_PrefLoc=1"
    
    html = await fetch_page(session, url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    
    try:
        # Find all search result items
        items = soup.select('li.s-item')
        
        for item in items[:max_listings]:
            # Skip if it's the first "result" which is usually an ad/header
            if 'srp-river-results-null-search__item' in item.get('class', []):
                continue
                
            # Extract title
            title_elem = item.select_one('.s-item__title')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            if 'Shop on eBay' in title or not title:
                continue
                
            # Extract price
            price_elem = item.select_one('.s-item__price')
            if not price_elem:
                continue
                
            price_text = price_elem.get_text(strip=True)
            # Handle price ranges (take the average)
            if ' to ' in price_text:
                prices = price_text.replace('$', '').replace(',', '').split(' to ')
                try:
                    price = (float(prices[0]) + float(prices[1])) / 2
                except:
                    continue
            else:
                # Extract the numeric part of the price
                price_match = re.search(r'(\d+,)*\d+\.\d+', price_text.replace('$', ''))
                if not price_match:
                    continue
                try:
                    price = float(price_match.group(0).replace(',', ''))
                except:
                    continue
            
            # Skip extreme prices (sanity check)
            if price <= 0.99 or price > 30000:
                continue
                
            # Extract link
            link_elem = item.select_one('a.s-item__link')
            if not link_elem:
                continue
            link = link_elem['href'].split('?')[0]
            
            # Make sure it's a direct listing link, not a search
            if not link or "/itm/" not in link:
                continue
            
            # Extract image URL
            img_elem = item.select_one('.s-item__image-img')
            img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
            
            # Replace eBay's lazy-loaded image placeholder
            if 'ir.ebaystatic.com' in img_url:
                img_url = img_elem.get('data-src', '')
            
            # Extract condition
            condition_elem = item.select_one('.SECONDARY_INFO')
            condition = condition_elem.get_text(strip=True) if condition_elem else "New"
            
            # Extract model numbers for better matching
            model_numbers = extract_model_numbers(title)
            
            # Add to listings
            listings.append({
                'title': title,
                'price': price,
                'link': link,
                'image_url': img_url,
                'normalized_title': normalize_title(title),
                'model_numbers': model_numbers,
                'condition': condition,
                'source': 'eBay',
                'keyword': keyword
            })
    except Exception as e:
        logger.error(f"Error parsing eBay results for {keyword}: {str(e)}")
    
    return listings

def calculate_similarity(item1, item2):
    """Calculate similarity between two items based on multiple factors."""
    title1 = item1['normalized_title']
    title2 = item2['normalized_title']
    
    # Base title similarity
    title_similarity = SequenceMatcher(None, title1, title2).ratio()
    
    # Initialize overall similarity score
    similarity = title_similarity * 0.7  # Title is 70% of the score
    
    # Check for model number matches (important for electronics, etc.)
    model_numbers1 = item1.get('model_numbers', [])
    model_numbers2 = item2.get('model_numbers', [])
    
    model_match_bonus = 0
    if model_numbers1 and model_numbers2:
        for model1 in model_numbers1:
            if any(model1 == model2 for model2 in model_numbers2):
                model_match_bonus = 0.3  # Exact model match is a strong signal
                break
    
    # Add model match bonus (caps at 1.0)
    similarity = min(1.0, similarity + model_match_bonus)
    
    return similarity

def find_arbitrage_opportunities(low_priced, high_priced):
    """Find arbitrage opportunities with optimal matching algorithm."""
    opportunities = []
    
    for low in low_priced:
        for high in high_priced:
            # Skip if same listing (same URL)
            if low['link'] == high['link']:
                continue
                
            # Calculate similarity
            similarity = calculate_similarity(low, high)
            
            # Only consider items that meet our similarity threshold
            if similarity >= SIMILARITY_THRESHOLD:
                buy_price = low['price']
                sell_price = high['price']
                
                # Skip if sell price isn't higher
                if sell_price <= buy_price:
                    continue
                
                # Calculate profit metrics
                profit = sell_price - buy_price
                profit_percentage = (profit / buy_price) * 100
                
                # Skip if profit is too low
                if profit_percentage < MIN_PROFIT_PERCENTAGE or profit < MIN_PROFIT_DOLLARS:
                    continue
                
                # Calculate confidence based on similarity and profit
                base_confidence = similarity * 85
                profit_bonus = min(15, profit_percentage / 10)  # Max 15% from profit
                confidence = min(99, base_confidence + profit_bonus)
                
                # Create opportunity object
                opportunity = {
                    'title': low['title'],
                    'buyPrice': buy_price,
                    'sellPrice': sell_price,
                    'buyLink': low['link'],
                    'sellLink': high['link'],
                    'profit': profit,
                    'profitPercentage': profit_percentage,
                    'confidence': round(confidence),
                    'similarity': similarity,
                    'image_url': low.get('image_url') or high.get('image_url', ''),
                    'subcategory': low.get('keyword', ''),
                    'buyCondition': low.get('condition', 'Unknown'),
                    'sellCondition': high.get('condition', 'Unknown')
                }
                
                opportunities.append(opportunity)
    
    return opportunities

async def process_subcategory(session, subcategory, semaphore):
    """Process a subcategory to find arbitrage opportunities."""
    async with semaphore:
        keywords = generate_keywords(subcategory)
        logger.info(f"Processing subcategory: {subcategory} with {len(keywords)} keywords")
        
        all_opportunities = []
        keyword_tasks = []
        
        # Create tasks for all keywords
        for keyword in keywords:
            # Create tasks for searching both price ranges concurrently
            keyword_tasks.append(asyncio.create_task(
                process_keyword(session, keyword, subcategory)
            ))
        
        # Run all keyword tasks and collect results
        keyword_results = await asyncio.gather(*keyword_tasks)
        
        # Combine all results
        for result in keyword_results:
            all_opportunities.extend(result)
        
        # Sort by profit percentage and return top results
        sorted_opps = sorted(all_opportunities, key=lambda x: -x['profitPercentage'])
        
        # Return only the best opportunities
        return sorted_opps[:MAX_RESULTS_PER_SUBCATEGORY]

async def process_keyword(session, keyword, subcategory):
    """Process a single keyword to find arbitrage opportunities."""
    try:
        logger.info(f"Searching for: {keyword}")
        
        # Search for low and high priced listings concurrently
        low_task = asyncio.create_task(search_ebay_listings(session, keyword, sort="price_asc"))
        high_task = asyncio.create_task(search_ebay_listings(session, keyword, sort="price_desc"))
        
        low_priced, high_priced = await asyncio.gather(low_task, high_task)
        
        if not low_priced or not high_priced:
            return []
        
        # Find arbitrage opportunities
        opportunities = find_arbitrage_opportunities(low_priced, high_priced)
        
        # Tag opportunities with subcategory info
        for opp in opportunities:
            opp['subcategory'] = subcategory
            
        return opportunities
    except Exception as e:
        logger.error(f"Error processing keyword {keyword}: {str(e)}")
        return []

async def run_arbitrage_scan_async(subcategories):
    """Run the arbitrage scan with optimized concurrency control."""
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, limit_per_host=8)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create a semaphore to limit concurrent subcategory processing
        semaphore = asyncio.Semaphore(min(len(subcategories), 5))
        
        # Process each subcategory with controlled concurrency
        subcategory_tasks = [
            process_subcategory(session, subcat, semaphore) 
            for subcat in subcategories
        ]
        
        # Run all subcategory tasks
        results = await asyncio.gather(*subcategory_tasks)
        
        # Combine all results
        all_opportunities = []
        for result in results:
            all_opportunities.extend(result)
        
        # Filter out duplicates (same buy/sell pair)
        unique_opportunities = []
        seen_pairs = set()
        
        for opp in all_opportunities:
            pair_key = (opp['buyLink'], opp['sellLink'])
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                unique_opportunities.append(opp)
        
        # Sort by profit percentage
        sorted_opps = sorted(unique_opportunities, key=lambda x: -x['profitPercentage'])
        
        # Return only the best opportunities, but keep diversity by subcategory
        # First, get top results from each subcategory
        final_results = []
        subcategory_included = set()
        
        # First pass: include top results from each subcategory
        for opp in sorted_opps:
            if opp['subcategory'] not in subcategory_included and len(final_results) < len(subcategories) * 2:
                final_results.append(opp)
                subcategory_included.add(opp['subcategory'])
        
        # Second pass: include remaining top results
        for opp in sorted_opps:
            if opp not in final_results and len(final_results) < 10:
                final_results.append(opp)
        
        return final_results

def run_arbitrage_scan(subcategories):
    """Run the arbitrage scan synchronously (wrapper for async function)."""
    start_time = time.time()
    logger.info(f"Starting scan for {len(subcategories)} subcategories: {subcategories}")
    
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async scan
        results = loop.run_until_complete(run_arbitrage_scan_async(subcategories))
        
        end_time = time.time()
        logger.info(f"Scan completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Found {len(results)} arbitrage opportunities")
        
        return results
    except Exception as e:
        logger.error(f"Error in arbitrage scan: {str(e)}")
        return []
    finally:
        # Clean up the event loop
        try:
            loop.close()
        except:
            pass

if __name__ == "__main__":
    # Test the scanner with a single subcategory
    test_subcategories = ["Magic: The Gathering"]
    results = run_arbitrage_scan(test_subcategories)
    
    # Print the results
    print(f"\nFound {len(results)} arbitrage opportunities:")
    for i, opportunity in enumerate(results[:5], 1):
        print(f"\nOpportunity #{i}:")
        print(f"Title: {opportunity['title']}")
        print(f"Buy Price: ${opportunity['buyPrice']:.2f}")
        print(f"Sell Price: ${opportunity['sellPrice']:.2f}")
        print(f"Profit: ${opportunity['profit']:.2f} ({opportunity['profitPercentage']:.2f}%)")
        print(f"Confidence: {opportunity['confidence']}%")
        print(f"Buy Link: {opportunity['buyLink']}")
        print(f"Sell Link: {opportunity['sellLink']}")

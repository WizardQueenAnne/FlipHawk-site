import random
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import time
from difflib import SequenceMatcher

async def fetch_page(session, url):
    """Fetch a page and return the HTML content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Error fetching {url}: Status code {response.status}")
                return None
    except Exception as e:
        print(f"Exception fetching {url}: {str(e)}")
        return None

def normalize_title(title):
    """Normalize title for better comparison."""
    # Convert to lowercase
    title = title.lower()
    
    # Remove common filler words and phrases
    fillers = ['brand new', 'new', 'sealed', 'mint', 'condition', 'authentic', 
               'genuine', 'official', 'in box', 'inbox', 'with box', 'unopened', 
               'fast shipping', 'free shipping', 'ships fast', 'lot of', 'set of',
               'excellent', 'great', 'like new', 'oem', 'original', 'factory',
               'bundle', 'rare', 'htf', 'hard to find', 'limited', 'exclusive',
               'complete', '100%', 'perfect', 'amazing', 'clean', 'tested',
               'working', 'fully functional', 'guaranteed', 'warranty']
    
    for filler in fillers:
        title = title.replace(filler, '')
    
    # Remove special characters and extra spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def extract_model_numbers(title):
    """Extract potential model numbers from a title for more precise matching."""
    # Common model number patterns (alphanumeric with dashes, dots, etc.)
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

def generate_keywords(subcategory):
    """Generate search keyword variations for a subcategory."""
    keywords = [subcategory]
    
    # Add common variations and related terms
    variations = {
        "Laptops": ["Laptop computer", "Notebook computer", "Portable computer", "Laptop PC", "Ultrabook", 
                   "MacBook", "ThinkPad", "Dell XPS", "HP Spectre", "Asus ZenBook", "Gaming laptop"],
        "Smartphones": ["Cell phone", "Mobile phone", "Smart phone", "iPhone", "Android phone", "Galaxy phone", 
                       "Google Pixel", "OnePlus", "Xiaomi", "Unlocked phone", "5G phone"],
        "Tablets": ["Tablet computer", "iPad", "Android tablet", "Galaxy Tab", "Surface tablet", 
                   "iPad Pro", "iPad Air", "Kindle Fire", "Drawing tablet", "E-reader"],
        "Headphones": ["Wireless headphones", "Earbuds", "AirPods", "Over-ear headphones", "Noise cancelling headphones", 
                      "Bluetooth headphones", "Gaming headset", "Studio headphones", "Sony WH", "Bose QuietComfort"],
        "Gaming Consoles": ["PlayStation", "Xbox", "Nintendo Switch", "Video game console", "Gaming system", 
                           "PS5", "Xbox Series X", "PlayStation 4", "Xbox One", "Nintendo", "Steam Deck"],
        "Computer Parts": ["CPU", "GPU", "Graphics card", "Computer memory", "SSD", "Hard drive", "Motherboard", 
                          "Power supply", "RAM", "RTX", "Radeon", "Intel", "AMD", "Corsair", "NVIDIA"],
        "Cameras": ["Digital camera", "DSLR", "Mirrorless camera", "Action camera", "Camera body", 
                   "Canon", "Nikon", "Sony Alpha", "Fujifilm", "GoPro", "Camera lens"],
        "Smartwatches": ["Smart watch", "Apple Watch", "Fitness tracker", "Garmin watch", "Wearable tech", 
                        "Samsung Galaxy Watch", "Fitbit", "Smart band", "GPS watch", "Sport watch"],
        "Bluetooth Speakers": ["Wireless speaker", "Portable speaker", "Smart speaker", "Bluetooth audio", 
                              "JBL", "Bose", "Sonos", "Battery speaker", "Waterproof speaker", "Sony speaker"],
        
        "Action Figures": ["Collectible figure", "Statue figure", "Toy figure", "Character figure", 
                          "Marvel figure", "DC figure", "Star Wars figure", "Funko Pop", "NECA figure", "McFarlane"],
        "Comic Books": ["Comics", "Graphic novel", "Comic collection", "Vintage comic", 
                       "Marvel comic", "DC comic", "Image comics", "First issue", "Key issue", "Comic lot"],
        "Coins": ["Collectible coins", "Rare coins", "Silver coins", "Gold coins", "Numismatic", 
                 "Proof coin", "Ancient coin", "Morgan dollar", "Bullion coin", "Mint coin", "Commemorative coin"],
        "Stamps": ["Postage stamps", "Stamp collection", "Rare stamps", "Philately", 
                  "First day cover", "Mint stamps", "Used stamps", "Vintage stamps", "Foreign stamps"],
        "Vinyl Records": ["LP records", "Albums vinyl", "Vintage vinyl", "Record collection", 
                         "33 RPM", "45 RPM", "First pressing", "Rare vinyl", "Limited edition vinyl", "Colored vinyl"],
        "Movie Memorabilia": ["Film memorabilia", "Movie props", "Cinema collectibles", "Movie posters", 
                             "Autographed movie", "Film cell", "Original poster", "Movie script", "Screen used"],
        "Vintage Toys": ["Retro toys", "Classic toys", "Old toys", "Collectible toys", "Antique toys", 
                        "80s toys", "90s toys", "Vintage action figures", "Vintage dolls", "Transformers G1"],
        "Autographs": ["Signed memorabilia", "Celebrity signature", "Autographed", "Signed photos", 
                      "Sports autograph", "Music autograph", "COA", "Authenticated", "JSA", "PSA/DNA"],
        
        "Magic: The Gathering": ["MTG", "Magic The Gathering", "Magic cards", "MtG cards", "MTG rare", "Magic booster", 
                                "MTG singles", "MTG lot", "Magic foil", "Commander deck", "Mythic rare", "Black Lotus"],
        "Pokémon": ["Pokemon", "Pokemon cards", "Pokemon TCG", "Pokemon Trading Card Game", "Pokemon rare", 
                   "Pokemon booster", "Pokemon lot", "Pokemon collection", "Charizard", "PSA Pokemon", "WOTC Pokemon"],
        "Yu-Gi-Oh!": ["Yugioh", "Yu Gi Oh", "YGO", "Yu-Gi-Oh cards", "Yugioh rare", 
                     "Yugioh lot", "YGO collection", "Konami TCG", "First edition yugioh", "Yugioh secret rare"],
        "Baseball Cards": ["MLB cards", "Baseball trading cards", "Vintage baseball cards", "Topps baseball", 
                          "Rookie card", "Autograph baseball card", "Bowman baseball", "Panini baseball", "Relic card"],
        "Football Cards": ["NFL cards", "Football trading cards", "Vintage football cards", 
                          "Rookie card NFL", "Auto football card", "Panini football", "Donruss football"],
        "Basketball Cards": ["NBA cards", "Basketball trading cards", "Vintage basketball cards", 
                            "Rookie card NBA", "Panini basketball", "Topps basketball", "Jordan card"],
        "Soccer Cards": ["FIFA cards", "Football trading cards", "Soccer trading cards", 
                        "Panini soccer", "Topps Match Attax", "World Cup cards", "Premier League cards"],
        "Hockey Cards": ["NHL cards", "Hockey trading cards", "Vintage hockey cards", 
                        "Upper Deck hockey", "The Cup hockey", "Rookie hockey card", "Gretzky card"],
        
        "Denim": ["Jeans", "Denim pants", "Vintage jeans", "Designer jeans", "Denim jacket", 
                 "Levi's", "Wrangler", "Selvedge denim", "Raw denim", "Slim fit jeans", "Straight leg jeans"],
        "T-Shirts": ["Tee shirts", "Graphic tees", "Vintage t-shirts", "Band t-shirts", "Designer t-shirts", 
                    "Concert shirt", "Rare t-shirt", "Single stitch", "80s t-shirt", "90s t-shirt"],
        "Jackets": ["Coat", "Outerwear", "Vintage jacket", "Designer jacket", "Leather jacket", 
                   "Bomber jacket", "Trucker jacket", "Varsity jacket", "Military jacket", "Ski jacket"],
        "Dresses": ["Vintage dress", "Designer dress", "Evening gown", "Cocktail dress", 
                   "Maxi dress", "Midi dress", "Wedding dress", "Summer dress", "Party dress"],
        "Sweaters": ["Pullover", "Cardigan", "Vintage sweater", "Designer sweater", "Knit sweater", 
                    "Cashmere sweater", "Wool sweater", "Crewneck", "Cozy sweater", "Cable knit"],
        "Band Merch": ["Concert merch", "Music merchandise", "Band t-shirt", "Tour merch", 
                      "Rock band", "Metal band", "Rap merch", "Vintage band", "Artist merchandise"],
        "Designer Items": ["Luxury clothing", "High-end fashion", "Designer brand", "Couture", 
                          "Gucci", "Louis Vuitton", "Prada", "Chanel", "Saint Laurent", "Designer purse"],
        "Activewear": ["Athletic wear", "Gym clothes", "Workout gear", "Sports apparel", 
                      "Nike", "Adidas", "Under Armour", "Lululemon", "Running clothes", "Yoga pants"],
        
        "Sneakers": ["Athletic shoes", "Running shoes", "Designer sneakers", "Collectible sneakers", "Rare sneakers", 
                    "Nike", "Air Jordan", "Adidas", "Yeezy", "New Balance", "Off-White", "Dunk low", "Vintage sneakers"],
        "Boots": ["Winter boots", "Leather boots", "Combat boots", "Designer boots", "Hiking boots", 
                 "Dr. Martens", "Timberland", "Chelsea boots", "Cowboy boots", "Work boots", "Engineer boots"],
        "Dress Shoes": ["Formal shoes", "Oxford shoes", "Men's dress shoes", "Women's heels", "Designer dress shoes", 
                       "Loafers", "Wingtips", "Brogues", "Leather dress shoes", "Italian shoes", "Church's shoes"],
        "Athletic Shoes": ["Sport shoes", "Running shoes", "Training shoes", "Workout shoes", 
                          "Basketball shoes", "Cross trainers", "Tennis shoes", "Track spikes", "Gym shoes"],
        "Designer Shoes": ["Luxury shoes", "High-end shoes", "Designer brand shoes", "Fashion shoes", 
                          "Gucci shoes", "Prada shoes", "Louboutin", "Jimmy Choo", "Balenciaga", "Ferragamo"],
        "Limited Edition": ["Rare shoes", "Exclusive release", "Limited release", "Special edition", 
                           "Collaboration shoes", "Numbered release", "Drop release", "Collector's edition"],
        "Vintage": ["Retro shoes", "Classic shoes", "Old school shoes", "Vintage footwear", 
                   "70s shoes", "80s shoes", "90s shoes", "Made in USA", "Made in England", "Original release"],
        "Sandals": ["Flip flops", "Summer shoes", "Beach sandals", "Designer sandals", 
                   "Birkenstock", "Teva", "Leather sandals", "Sport sandals", "Slide sandals", "Comfort sandals"],
    }
    
    # Add subcategory-specific variations
    if subcategory in variations:
        keywords.extend(variations[subcategory])
    
    return keywords

async def search_ebay_listings(session, keyword, sort="price_asc"):
    """Search eBay listings with the given keyword and sort order."""
    encoded_keyword = keyword.replace(" ", "+")
    
    # Determine sort parameter
    sort_param = "15" if sort == "price_asc" else "16"  # 15=price+shipping: lowest first, 16=price+shipping: highest first
    
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_keyword}&_sop={sort_param}&LH_BIN=1&LH_ItemCondition=1000"
    
    html = await fetch_page(session, url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    
    # Find all search result items
    items = soup.select('li.s-item')
    
    for item in items[:20]:  # Limit to first 20 results
        # Skip if it's the first "result" which is usually an ad/header
        if 'srp-river-results-null-search__item' in item.get('class', []):
            continue
            
        # Extract title
        title_elem = item.select_one('.s-item__title')
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        if 'Shop on eBay' in title:
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
                
        # Extract link
        link_elem = item.select_one('a.s-item__link')
        if not link_elem:
            continue
        link = link_elem['href'].split('?')[0]
        
        # Extract image URL
        img_elem = item.select_one('.s-item__image-img')
        img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
        
        # Replace eBay's lazy-loaded image placeholder
        if 'ir.ebaystatic.com' in img_url:
            # Try to get real image
            img_url = img_elem.get('data-src', '')
        
        # Check if the item has free shipping
        shipping_elem = item.select_one('.s-item__shipping, .s-item__freeXDays')
        has_free_shipping = shipping_elem and 'Free' in shipping_elem.get_text(strip=True)
        
        # Extract model numbers for better matching
        model_numbers = extract_model_numbers(title)
        
        # Extract condition
        condition_elem = item.select_one('.SECONDARY_INFO')
        condition = condition_elem.get_text(strip=True) if condition_elem else "New"
        
        # Add to listings
        listings.append({
            'title': title,
            'price': price,
            'link': link,
            'image_url': img_url,
            'free_shipping': has_free_shipping,
            'normalized_title': normalize_title(title),
            'model_numbers': model_numbers,
            'condition': condition,
            'source': 'eBay',
            'keyword': keyword,
            'subcategory': keyword
        })
    
    return listings

def calculate_similarity(title1, title2, model_numbers1=None, model_numbers2=None):
    """Calculate similarity between two titles using SequenceMatcher and model numbers."""
    base_similarity = SequenceMatcher(None, title1, title2).ratio()
    
    # Enhanced similarity check with model numbers if available
    if model_numbers1 and model_numbers2:
        # Check if any model numbers match exactly
        for model1 in model_numbers1:
            if any(model1 == model2 for model2 in model_numbers2):
                # If model numbers match exactly, boost similarity
                return min(1.0, base_similarity + 0.2)
    
    return base_similarity

def filter_listings_by_condition(listings):
    """Filter listings to prefer items in better condition."""
    condition_priority = {
        "New": 1,
        "Brand New": 1,
        "New with tags": 2,
        "New with box": 2,
        "New without tags": 3,
        "New without box": 3
    }
    
    # Add a condition score to each listing
    for listing in listings:
        condition = listing.get('condition', 'Unknown')
        listing['condition_score'] = condition_priority.get(condition, 5)  # Default to lower priority
    
    return listings

def find_arbitrage_opportunities(low_priced, high_priced, similarity_threshold=0.75):
    """Find arbitrage opportunities by comparing low and high-priced listings."""
    opportunities = []
    
    # Filter listings by condition
    low_priced = filter_listings_by_condition(low_priced)
    high_priced = filter_listings_by_condition(high_priced)
    
    for low in low_priced:
        for high in high_priced:
            # Skip if comparing the same item (same URL)
            if low['link'] == high['link']:
                continue
                
            # Calculate similarity between the titles
            similarity = calculate_similarity(
                low['normalized_title'], 
                high['normalized_title'],
                low.get('model_numbers', []),
                high.get('model_numbers', [])
            )
            
            if similarity >= similarity_threshold:
                # Calculate profit metrics
                buy_price = low['price']
                sell_price = high['price']
                profit = sell_price - buy_price
                profit_percentage = (profit / buy_price) * 100
                
                # Skip if profit is too low or negative
                if profit_percentage < 20 or profit < 10:
                    continue
                
                # Apply condition-based confidence adjustment
                condition_adjustment = 0
                if low['condition_score'] <= high['condition_score']:
                    # Better to have equal or better condition when buying vs selling
                    condition_adjustment = 5
                else:
                    # If selling condition is better than buying condition, that's suspicious
                    condition_adjustment = -10
                
                # Calculate confidence score based on similarity, profit, and condition
                base_confidence = similarity * 80  # Max 80% from title similarity
                profit_bonus = min(10, profit_percentage / 10)  # Max 10% from profit
                
                # Final confidence calculation
                confidence = min(95, base_confidence + profit_bonus + condition_adjustment)
                confidence = max(50, confidence)  # Minimum confidence of 50%
                
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
                    'image_url': low['image_url'] or high['image_url'],
                    'subcategory': low['subcategory'],
                    'keyword': low['keyword']
                }
                
                opportunities.append(opportunity)
    
    return opportunities

async def process_subcategory(session, subcategory):
    """Process a single subcategory to find arbitrage opportunities."""
    keywords = generate_keywords(subcategory)
    all_opportunities = []
    
    for keyword in keywords:
        print(f"Searching for: {keyword}")
        
        try:
            # Fetch listings sorted by price (ascending and descending)
            low_priced_listings = await search_ebay_listings(session, keyword, sort="price_asc")
            # Artificial delay to prevent rate limiting
            await asyncio.sleep(1)
            high_priced_listings = await search_ebay_listings(session, keyword, sort="price_desc")
            
            if low_priced_listings and high_priced_listings:
                opportunities = find_arbitrage_opportunities(low_priced_listings, high_priced_listings)
                for opp in opportunities:
                    opp['subcategory'] = subcategory
                    opp['keyword'] = keyword
                all_opportunities.extend(opportunities)
        except Exception as e:
            print(f"Error processing keyword '{keyword}': {str(e)}")
            continue
    
    return all_opportunities

async def fetch_all_arbitrage_opportunities(subcategories):
    """Fetch arbitrage opportunities for all subcategories."""
    async with aiohttp.ClientSession() as session:
        tasks = [process_subcategory(session, subcat) for subcat in subcategories]
        results = await asyncio.gather(*tasks)
    
    # Combine results from all subcategories
    all_opportunities = []
    for result in results:
        all_opportunities.extend(result)
    
    # Filter out potential duplicates (same buy/sell links)
    unique_opportunities = []
    seen_pairs = set()
    
    for opp in all_opportunities:
        pair_key = (opp['buyLink'], opp['sellLink'])
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_opportunities.append(opp)
    
    # Sort by profit percentage and return top results (limit to 20)
    sorted_opportunities = sorted(unique_opportunities, key=lambda x: -x['profitPercentage'])
    
    # Take top 20 but ensure diversity by including at least one from each subcategory if available
    result = []
    subcategory_included = set()
    
    # First pass: include top results from each subcategory
    for opp in sorted_opportunities:
        if opp['subcategory'] not in subcategory_included and len(result) < 10:
            result.append(opp)
            subcategory_included.add(opp['subcategory'])
    
    # Second pass: include remaining top results
    for opp in sorted_opportunities:
        if opp not in result and len(result) < 20:
            result.append(opp)
    
    return result[:20]

def generate_simulated_opportunities(subcategories):
    """
    Generate simulated arbitrage opportunities for demonstration purposes.
    This is used when no real arbitrage opportunities are found.
    """
    simulated = []
    
    product_templates = {
        "Laptops": [
            {"name": "Dell XPS 13 9310 13.4 inch FHD+ Laptop", "low": 699, "high": 999, "image": "laptop_dell.jpg"},
            {"name": "MacBook Air M1 8GB RAM 256GB SSD", "low": 749, "high": 999, "image": "laptop_macbook.jpg"},
            {"name": "Lenovo ThinkPad X1 Carbon Gen 9", "low": 899, "high": 1349, "image": "laptop_lenovo.jpg"},
            {"name": "ASUS ROG Zephyrus G14 Gaming Laptop", "low": 1099, "high": 1499, "image": "laptop_asus.jpg"},
            {"name": "HP Spectre x360 2-in-1 Ultrabook", "low": 849, "high": 1199, "image": "laptop_hp.jpg"},
            {"name": "Razer Blade 15 Gaming Laptop", "low": 1299, "high": 1799, "image": "laptop_razer.jpg"}
        ],
        "Smartphones": [
            {"name": "iPhone 13 Pro 128GB Graphite Unlocked", "low": 699, "high": 899, "image": "phone_iphone.jpg"},
            {"name": "Samsung Galaxy S21 Ultra 5G 128GB", "low": 649, "high": 899, "image": "phone_samsung.jpg"},
            {"name": "Google Pixel 6 Pro 128GB", "low": 499, "high": 749, "image": "phone_pixel.jpg"},
            {"name": "OnePlus 9 Pro 5G 256GB", "low": 599, "high": 799, "image": "phone_oneplus.jpg"},
            {"name": "iPhone 12 Mini 64GB Unlocked", "low": 399, "high": 599, "image": "phone_iphone12.jpg"},
            {"name": "Samsung Galaxy Z Flip 3 128GB", "low": 699, "high": 949, "image": "phone_flip.jpg"}
        ],
        "Pokémon": [
            {"name": "Charizard VMAX Rainbow Rare 074/073", "low": 149, "high": 249, "image": "pokemon_charizard.jpg"},
            {"name": "Booster Box Pokémon Brilliant Stars Sealed", "low": 99, "high": 159, "image": "pokemon_box.jpg"},
            {"name": "Pikachu VMAX Rainbow Rare 188/185", "low": 129, "high": 219, "image": "pokemon_pikachu.jpg"},
            {"name": "Ancient Mew Sealed Promo Card", "low": 39, "high": 89, "image": "pokemon_mew.jpg"},
            {"name": "Umbreon VMAX Alternate Art 215/203", "low": 279, "high": 399, "image": "pokemon_umbreon.jpg"},
            {"name": "Celebrations Ultra Premium Collection Box", "low": 199, "high": 349, "image": "pokemon_celebrations.jpg"}
        ],
        "Magic: The Gathering": [
            {"name": "Liliana of the Veil Innistrad Mythic", "low": 49, "high": 89, "image": "mtg_liliana.jpg"},
            {"name": "Jace, the Mind Sculptor Worldwake", "low": 99, "high": 189, "image": "mtg_jace.jpg"},
            {"name": "Tarmogoyf Modern Horizons 2", "low": 29, "high": 59, "image": "mtg_tarmogoyf.jpg"},
            {"name": "Mana Crypt Eternal Masters", "low": 159, "high": 259, "image": "mtg_manacrypt.jpg"},
            {"name": "Ragavan, Nimble Pilferer Modern Horizons 2", "low": 69, "high": 115, "image": "mtg_ragavan.jpg"},
            {"name": "Collector Booster Box Modern Horizons 3", "low": 229, "high": 349, "image": "mtg_box.jpg"}
        ],
        "Yu-Gi-Oh!": [
            {"name": "Blue-Eyes White Dragon 1st Edition", "low": 79, "high": 149, "image": "yugioh_blueeyes.jpg"},
            {"name": "Dark Magician Girl 1st Edition", "low": 69, "high": 119, "image": "yugioh_darkmagician.jpg"},
            {"name": "Accesscode Talker Prismatic Secret Rare", "low": 59, "high": 99, "image": "yugioh_accesscode.jpg"},
            {"name": "Ash Blossom & Joyous Spring Ultra Rare", "low": 29, "high": 49, "image": "yugioh_ash.jpg"},
            {"name": "Ghost Rare Stardust Dragon", "low": 149, "high": 249, "image": "yugioh_stardust.jpg"},
            {"name": "Pot of Prosperity Secret Rare", "low": 79, "high": 129, "image": "yugioh_pot.jpg"}
        ],
        "Sneakers": [
            {"name": "Nike Air Jordan 1 Retro High OG", "low": 189, "high": 299, "image": "sneakers_jordan1.jpg"},
            {"name": "Adidas Yeezy Boost 350 V2", "low": 219, "high": 349, "image": "sneakers_yeezy.jpg"},
            {"name": "Nike Dunk Low Retro White Black", "low": 99, "high": 179, "image": "sneakers_dunk.jpg"},
            {"name": "New Balance 550 White Green", "low": 89, "high": 159, "image": "sneakers_nb.jpg"},
            {"name": "Nike SB Dunk Low Travis Scott", "low": 899, "high": 1299, "image": "sneakers_travis.jpg"},
            {"name": "Air Jordan 4 Retro University Blue", "low": 299, "high": 449, "image": "sneakers_jordan4.jpg"}
        ],

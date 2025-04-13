from flask import Flask, request, jsonify
import time
import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArbitrageBot")

CATEGORY_KEYWORDS = {
    "trading cards": ["yugioh", "magic the gathering", "pokemon", "baseball cards", "football cards", "soccer cards"],
    "collectibles": ["action figures", "rare coins", "stamps", "comic books"],
    "antiques": ["antique lamp", "vintage clock", "old radio"],
    "tech": ["laptop", "tablet", "smartphone", "camera", "headphones"]
}

SCAN_DURATION = 60  # shorter for testing
CHECK_INTERVAL = 10

def fetch_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return None

def parse_item_from_ebay(url, keyword):
    html = fetch_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for listing in soup.select(".s-item"):
        try:
            title_tag = listing.select_one(".s-item__title")
            price_tag = listing.select_one(".s-item__price")
            link_tag = listing.select_one("a.s-item__link")
            if not title_tag or not price_tag or not link_tag:
                continue
            title = title_tag.text
            price_text = price_tag.text.replace("$", "").replace(",", "").split()[0]
            price = float(price_text)
            link = link_tag["href"]
            if keyword.lower() in title.lower():
                items.append({
                    "title": title,
                    "price": price,
                    "url": link,
                    "platform": "eBay"
                })
        except Exception as e:
            logger.warning(f"Error parsing listing: {e}")
    return items

def find_arbitrage_opportunities(all_items):
    seen_deals = set()
    top_deals = []
    for keyword, items in all_items.items():
        sorted_items = sorted(items, key=lambda x: x['price'])
        if len(sorted_items) < 2:
            continue
        cheapest = sorted_items[0]
        for comp in sorted_items[1:]:
            price_diff = comp["price"] - cheapest["price"]
            percent_diff = (price_diff / cheapest["price"]) * 100
            deal_id = (cheapest["url"], comp["url"])
            if percent_diff > 20 and deal_id not in seen_deals:
                seen_deals.add(deal_id)
                deal_info = {
                    "keyword": keyword,
                    "item1": cheapest,
                    "item2": comp,
                    "profit": price_diff,
                    "percent": percent_diff
                }
                top_deals.append(deal_info)
                top_deals.sort(key=lambda d: d["profit"], reverse=True)
                if len(top_deals) > 10:
                    top_deals.pop()
    return top_deals

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    category = data.get("category", "").lower()
    keywords = CATEGORY_KEYWORDS.get(category, [])
    if not keywords:
        return jsonify({"error": "Invalid category"}), 400

    logger.info(f"🔎 Starting scan for category: {category}")
    start_time = time.time()
    all_items = {kw: [] for kw in keywords}
    while time.time() - start_time < SCAN_DURATION:
        for kw in keywords:
            logger.info(f"Searching for: {kw}")
            url = f"https://www.ebay.com/sch/i.html?_nkw={quote(kw)}"
            all_items[kw].extend(parse_item_from_ebay(url, kw))
        time.sleep(CHECK_INTERVAL)

    top_deals = find_arbitrage_opportunities(all_items)
    return jsonify(top_deals)

if __name__ == "__main__":
    app.run(debug=True)

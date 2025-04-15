import time
import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import logging

# --- LOGGER SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArbitrageBot")

# --- CONFIG ---
SCAN_DURATION = 60  # Total scan time (seconds)
CHECK_INTERVAL = 10  # Time between keyword scans (seconds)

# --- FETCH HTML WITH URLLIB ---
def fetch_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return None

# --- PARSE EBAY LISTINGS ---
def parse_ebay(keyword):
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote(keyword)}"
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
            url = link_tag["href"]

            items.append({
                "title": title,
                "price": price,
                "url": url,
                "platform": "eBay"
            })

        except Exception as e:
            logger.warning(f"Error parsing listing: {e}")
    return items

# --- COMPARE AND FIND DEALS ---
def analyze_deals(keyword, items, seen_deals, top_deals):
    sorted_items = sorted(items, key=lambda x: x["price"])
    if len(sorted_items) < 2:
        return

    cheapest = sorted_items[0]
    for comp in sorted_items[1:]:
        price_diff = comp["price"] - cheapest["price"]
        percent_diff = (price_diff / cheapest["price"]) * 100
        deal_id = (cheapest["url"], comp["url"])

        if percent_diff > 20 and deal_id not in seen_deals:
            seen_deals.add(deal_id)
            deal = {
                "keyword": keyword,
                "item1": cheapest,
                "item2": comp,
                "profit": round(price_diff, 2),
                "percent": round(percent_diff, 1)
            }
            top_deals.append(deal)
            top_deals.sort(key=lambda d: d["profit"], reverse=True)
            if len(top_deals) > 10:
                top_deals.pop()

# --- MAIN FUNCTION ---
def run_arbitrage_scan(keywords):
    logger.info(f"🚀 Running arbitrage scan for: {keywords}")
    start_time = time.time()
    seen_deals = set()
    top_deals = []

    while time.time() - start_time < SCAN_DURATION:
        for kw in keywords:
            logger.info(f"🔍 Scanning: {kw}")
            items = parse_ebay(kw)
            analyze_deals(kw, items, seen_deals, top_deals)
            time.sleep(CHECK_INTERVAL)

    logger.info(f"✅ Finished scanning. {len(top_deals)} top deals found.")
    return top_deals

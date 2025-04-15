import time
import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArbitrageBot")

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

def run_arbitrage_scan(keywords, scan_duration=30):
    start_time = time.time()
    seen_deals = set()
    top_deals = []

    logger.info("🚀 Running real-time scan...")

    all_items = {kw: [] for kw in keywords}

    for kw in keywords:
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(kw)}"
        all_items[kw].extend(parse_item_from_ebay(ebay_url, kw))

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
                    "profit": round(price_diff, 2),
                    "percent": round(percent_diff, 1)
                }
                top_deals.append(deal_info)
                top_deals.sort(key=lambda d: d["profit"], reverse=True)
                if len(top_deals) > 10:
                    top_deals.pop()
    return top_deals

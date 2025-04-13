import time
import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup

CATEGORY_KEYWORDS = {
    "trading cards": ["yugioh", "magic the gathering", "pokemon cards", "baseball cards", "football cards", "soccer cards"],
    "tech": ["laptop", "tablet", "smartphone", "headphones", "camera"],
    "collectibles": ["funko pop", "vintage toy", "rare coin", "signed memorabilia"],
    "antiques": ["antique clock", "vintage lamp", "old radio"],
}

def fetch_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except:
        return None

def parse_items(keyword):
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

            if not (title_tag and price_tag and link_tag):
                continue

            title = title_tag.text
            price_text = price_tag.text.replace("$", "").replace(",", "").split()[0]
            price = float(price_text)
            url = link_tag["href"]

            items.append({
                "title": title,
                "price": price,
                "url": url
            })
        except:
            continue

    return items

def find_deals(items_by_keyword):
    seen = set()
    top_deals = []

    for keyword, items in items_by_keyword.items():
        sorted_items = sorted(items, key=lambda x: x["price"])
        if len(sorted_items) < 2:
            continue
        low = sorted_items[0]
        for high in sorted_items[1:]:
            profit = high["price"] - low["price"]
            percent = (profit / low["price"]) * 100
            deal_id = (low["url"], high["url"])
            if percent > 20 and deal_id not in seen:
                seen.add(deal_id)
                top_deals.append({
                    "keyword": keyword,
                    "listing1": low,
                    "listing2": high,
                    "profit": round(profit, 2),
                    "confidence": round(percent, 1)
                })
                if len(top_deals) >= 10:
                    break
    return top_deals

def run_bot(category):
    keywords = CATEGORY_KEYWORDS.get(category.lower(), [])
    all_items = {kw: parse_items(kw) for kw in keywords}
    top_deals = find_deals(all_items)
    return top_deals

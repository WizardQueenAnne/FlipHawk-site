import time
import sys
import urllib.request
from urllib.parse import quote
from bs4 import BeautifulSoup

SCAN_DURATION = 60
CHECK_INTERVAL = 10

def fetch_html(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception:
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

            if not title_tag or not price_tag or not link_tag:
                continue

            title = title_tag.text
            price = float(price_tag.text.replace("$", "").replace(",", "").split()[0])
            link = link_tag["href"]

            items.append({"title": title, "price": price, "url": link})
        except:
            continue
    return items

def run_scan(keywords):
    all_items = {kw: parse_items(kw) for kw in keywords}
    seen = set()
    top_deals = []

    for kw, items in all_items.items():
        sorted_items = sorted(items, key=lambda x: x['price'])
        if len(sorted_items) < 2:
            continue

        for i in range(1, len(sorted_items)):
            cheap = sorted_items[0]
            comp = sorted_items[i]
            diff = comp["price"] - cheap["price"]
            percent = (diff / cheap["price"]) * 100
            ids = (cheap["url"], comp["url"])

            if percent > 20 and ids not in seen:
                seen.add(ids)
                top_deals.append((kw, cheap, comp, diff, percent))

    return top_deals

def main():
    keywords = sys.argv[1:]
    start = time.time()
    result_output = []

    while time.time() - start < SCAN_DURATION:
        top_deals = run_scan(keywords)
        if top_deals:
            for kw, item1, item2, profit, pct in top_deals:
                result_output.append(
                    f"\n📦 Category: {kw.upper()}\n"
                    f"🔗 1: {item1['title']} (${item1['price']})\n{item1['url']}\n"
                    f"🔗 2: {item2['title']} (${item2['price']})\n{item2['url']}\n"
                    f"💰 Profit: ${profit:.2f} ({pct:.1f}% margin)\n"
                    + "-"*50
                )
            break
        time.sleep(CHECK_INTERVAL)

    if not result_output:
        print("😕 No deals found right now.")
    else:
        print("\n".join(result_output))

if __name__ == "__main__":
    main()

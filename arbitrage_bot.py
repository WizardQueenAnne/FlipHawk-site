from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from time import time
import re

def extract_price(text):
    match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", text.replace(",", ""))
    return float(match.group(1)) if match else None

def fetch_ebay_listings(keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    query = keyword.replace(" ", "+")
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sop=15"
    req = Request(url, headers=headers)
    html = urlopen(req).read()
    soup = BeautifulSoup(html, "html.parser")

    listings = []
    seen_titles = set()

    for item in soup.select(".s-item"):
        title_elem = item.select_one(".s-item__title")
        price_elem = item.select_one(".s-item__price")
        link_elem = item.select_one("a.s-item__link")

        if not title_elem or not price_elem or not link_elem:
            continue

        title = title_elem.text.strip()
        price = extract_price(price_elem.text.strip())
        link = link_elem["href"]

        if title in seen_titles or not price:
            continue
        seen_titles.add(title)

        listings.append({
            "title": title,
            "price": price,
            "link": link
        })

    return listings

def run_arbitrage_scan(keywords):
    all_deals = []
    seen_links = set()

    for kw in keywords:
        listings = fetch_ebay_listings(kw)
        for listing in listings:
            if listing["link"] in seen_links:
                continue
            seen_links.add(listing["link"])
            confidence = 80 + (5 * keywords.index(kw) % 15)  # basic confidence estimate
            all_deals.append({
                "title": listing["title"],
                "price": listing["price"],
                "link": listing["link"],
                "confidence": confidence,
                "keyword": kw
            })

    sorted_deals = sorted(all_deals, key=lambda x: (-x["confidence"], x["price"]))
    return sorted_deals[:10]

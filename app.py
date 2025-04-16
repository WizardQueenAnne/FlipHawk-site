from flask import Flask, render_template, request, jsonify
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Mapping of subcategories to keywords
SUBCATEGORY_KEYWORDS = {
    "Comic Books": ["marvel comics", "vintage comic books", "dc comics", "rare comics"],
    "Jordans": ["air jordan 1", "air jordan retro", "nike jordan", "jordan sneakers"],
    "Headphones": ["wireless headphones", "noise cancelling headphones", "bluetooth headphones", "over ear headphones"]
}

@app.route('/')
def index():
    categories = list(SUBCATEGORY_KEYWORDS.keys())
    return render_template('index.html', categories=categories)

@app.route('/get_subcategories', methods=['POST'])
def get_subcategories():
    category = request.json.get('category')
    subcategories = list(SUBCATEGORY_KEYWORDS.keys())  # Assuming subcategories are the same as keys
    return jsonify({'subcategories': subcategories})

@app.route('/scan', methods=['POST'])
def scan():
    subcategory = request.json.get('subcategory')
    keywords = SUBCATEGORY_KEYWORDS.get(subcategory, [])
    results = asyncio.run(fetch_ebay_data(keywords))
    return jsonify({'results': results})

async def fetch_ebay_data(keywords):
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_items(session, keyword) for keyword in keywords]
        items_list = await asyncio.gather(*tasks)
        for keyword, items in zip(keywords, items_list):
            results[keyword] = items
    return results

async def fetch_items(session, keyword):
    url = f"https://www.ebay.com/sch/i.html?_nkw={keyword.replace(' ', '+')}&_ipg=100"
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return []
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            items = []
            for item in soup.select('.s-item'):
                title_elem = item.select_one('.s-item__title')
                price_elem = item.select_one('.s-item__price')
                if title_elem and price_elem:
                    title = title_elem.get_text()
                    price_text = price_elem.get_text()
                    price = parse_price(price_text)
                    items.append({'title': title, 'price': price})
            return items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def parse_price(price_text):
    # Remove any non-numeric characters except for the decimal point
    price_text = re.sub(r'[^\d.]', '', price_text)
    try:
        return float(price_text)
    except ValueError:
        return 0.0

if __name__ == '__main__':
    app.run(debug=True)

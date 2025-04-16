from flask import Flask, request, jsonify, send_from_directory
from arbitrage_bot import run_arbitrage_scan
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static')
CORS(app)

CATEGORY_KEYWORDS = {
    "Tech": {
        "Headphones": ["headphones", "wireless headphones", "Bluetooth headset"],
        "Laptops": ["laptop", "MacBook", "Chromebook"],
        "Smartphones": ["iPhone", "Android phone", "smartphone"],
    },
    "Collectibles": {
        "Pokemon Cards": ["pokemon card", "pokemon holo", "rare pokemon"],
        "MTG Cards": ["mtg card", "magic the gathering", "rare mtg"],
        "Comic Books": ["comic book", "marvel comic", "dc comic"],
    },
    "Vintage Clothing": {
        "Jordans": ["Air Jordans", "Jordan 1", "retro Jordans"],
        "Levi's Jeans": ["vintage levis", "levis 501", "levis denim"],
        "Band Tees": ["vintage band tee", "metallica shirt", "nirvana shirt"]
    }
}

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    category = data.get("category")
    subcategories = data.get("subcategories", [])

    if not subcategories:
        return jsonify({"error": "No subcategories selected."}), 400

    all_keywords = []
    for sub in subcategories:
        sub_keywords = CATEGORY_KEYWORDS.get(category, {}).get(sub, [])
        all_keywords.extend(sub_keywords)

    if not all_keywords:
        return jsonify({"error": "No valid keywords found for the selected subcategories."}), 400

    results = run_arbitrage_scan(all_keywords)
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

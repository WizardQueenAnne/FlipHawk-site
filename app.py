from flask import Flask, render_template, request, jsonify
from arbitrage_bot import run_arbitrage_scan

# Tell Flask to load templates from the root directory
app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    categories = {
        "Tech": ["Headphones", "Smartphones", "Laptops"],
        "Collectibles": ["Pokémon Cards", "MTG Cards", "Comics"],
        "Vintage Clothing": ["Jordans", "Graphic Tees", "Denim Jackets"]
    }
    return render_template('index.html', categories=categories)

@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    selected_subcategories = data.get('subcategories', [])
    if not selected_subcategories:
        return jsonify({"error": "No subcategories selected"}), 400

    results = run_arbitrage_scan(selected_subcategories)
    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True)

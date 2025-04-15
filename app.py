from flask import Flask, request, jsonify, render_template_string
from arbitrage_bot import run_arbitrage_scan

app = Flask(__name__)

# Load index.html manually since it's not in a 'templates/' folder
def get_index_html():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/")
def home():
    return render_template_string(get_index_html())

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    category = data.get("category")
    subcategories = data.get("subcategories", [])

    if not category or not subcategories:
        return jsonify({"error": "Missing category or subcategories"}), 400

    keywords = [category] + subcategories
    results = run_arbitrage_scan(keywords)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)


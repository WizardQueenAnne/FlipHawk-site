from flask import Flask, request, jsonify, render_template
from arbitrage_bot import run_arbitrage_scan  # adjusted for flat structure

app = Flask(__name__, static_folder='static', template_folder='static')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    category = data.get("category")
    subcategories = data.get("subcategories", [])

    if not category or not subcategories:
        return jsonify({"error": "Missing category or subcategories"}), 400

    # Combine category and subcategories for keyword scanning
    keywords = [category] + subcategories

    # Run scan and return results
    results = run_arbitrage_scan(keywords)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
from arbitrage_bot import run_arbitrage_scan  # Ensure this function can accept multiple subcategories

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search')
def search():
    category = request.args.get('category')
    subcategories = request.args.getlist('subcategories')

    if not category or not subcategories:
        return jsonify({"error": "No category or subcategories selected."}), 400

    # Pass the selected subcategories to your arbitrage bot logic
    deals = run_arbitrage_scan(category, subcategories)
    return jsonify(deals)

if __name__ == '__main__':
    app.run(debug=True)

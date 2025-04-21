from flask import Flask, send_from_directory, request, jsonify
import os
from arbitrage_bot import run_arbitrage_scan

app = Flask(__name__)

# Serve the index.html from the root directory
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

# Serve static files
@app.route('/styles.css')
def serve_css():
    return send_from_directory(os.getcwd(), 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory(os.getcwd(), 'script.js')

# API endpoint to run the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    try:
        data = request.get_json()
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])

        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required."}), 400

        # Call the scraper with keywords (subcategories)
        result = run_arbitrage_scan(subcategories)

        # Optionally include the number of deals found
        result['dealCount'] = len(result.get('deals', []))

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

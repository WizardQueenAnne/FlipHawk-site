from flask import Flask, send_from_directory, request, jsonify
import os
from arbitrage_bot import run_arbitrage_scan

# Initialize Flask app
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

# API endpoint for running the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    data = request.get_json()
    category = data.get('category', '')
    subcategories = data.get('subcategories', [])
    
    if not category or not subcategories:
        return jsonify({"error": "Category and subcategories are required"}), 400
    
    # Run the arbitrage scan with the subcategories as keywords
    result = run_arbitrage_scan(subcategories)
    return jsonify(result)

if __name__ == '__main__':
    # Use environment variable to specify the port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

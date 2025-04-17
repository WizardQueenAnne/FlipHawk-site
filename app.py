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
    
    # Map categories to keywords
    keywords_map = {
        'Tech': ['laptop', 'smartphone', 'headphones', 'tablet'],
        'Collectibles': ['pokemon cards', 'vintage toys', 'comic books', 'action figures'],
        'Vintage Clothing': ['vintage denim', 'retro sneakers', 'vintage jackets', 'band shirts']
    }
    
    keywords = keywords_map.get(category, [])
    if not keywords:
        return jsonify({"error": "Invalid category"}), 400
    
    # Run the arbitrage scan
    result = run_arbitrage_scan(keywords)
    return jsonify(result)

if __name__ == '__main__':
    # Use environment variable to specify the port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

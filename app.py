from flask import Flask, send_from_directory, request, jsonify
import os
import logging
from datetime import datetime
from arbitrage_bot import run_arbitrage_scan

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__)

# Ensure the static directory exists
static_dir = os.path.join(os.getcwd(), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

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

# Serve logo images
@app.route('/logo.png')
def serve_logo():
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'logo.png')

@app.route('/mini-logo.png')
def serve_mini_logo():
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'mini-logo.png')

# Simple scan stats tracker
scan_log = []

def log_scan(category, subcategories, results_count):
    """Log a scan for statistics purposes."""
    scan_entry = {
        "category": category,
        "subcategories": subcategories,
        "results_count": results_count,
        "timestamp": datetime.now().isoformat(),
    }
    scan_log.append(scan_entry)
    
    # Keep scan log at a reasonable size
    if len(scan_log) > 1000:
        scan_log.pop(0)

# API endpoint for running the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    """
    Run an arbitrage scan based on the selected category and subcategories.
    
    Expected JSON input:
    {
        "category": "Collectibles",
        "subcategories": ["Magic: The Gathering", "Pokémon"]
    }
    """
    try:
        data = request.get_json()
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        
        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required"}), 400
        
        # Log the scan request
        logger.info(f"Received scan request for category: {category}, subcategories: {subcategories}")
        
        # Run the arbitrage scan with the subcategories as keywords
        start_time = datetime.now()
        results = run_arbitrage_scan(subcategories)
        end_time = datetime.now()
        
        # Log scan time and results
        scan_duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan completed in {scan_duration:.2f} seconds with {len(results)} results")
        
        # Process results to include estimated tax and shipping
        for result in results:
            # Calculate estimated tax (around 8%)
            estimated_tax = result['buyPrice'] * 0.08
            result['estimatedTax'] = round(estimated_tax, 2)
            
            # Add estimated shipping (fixed amount for simplicity)
            estimated_shipping = 5.99
            result['estimatedShipping'] = estimated_shipping
            
            # Calculate net profit after tax and shipping
            total_cost = result['buyPrice'] + estimated_tax + estimated_shipping
            net_profit = result['sellPrice'] - total_cost
            net_profit_percentage = (net_profit / total_cost) * 100
            
            result['totalCost'] = round(total_cost, 2)
            result['netProfit'] = round(net_profit, 2)
            result['netProfitPercentage'] = round(net_profit_percentage, 2)
        
        # Log the scan for statistics
        log_scan(category, subcategories, len(results))
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}")
        return jsonify({"error": f"An error occurred while processing your request: {str(e)}"}), 500

if __name__ == '__main__':
    # Use environment variable to specify the port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

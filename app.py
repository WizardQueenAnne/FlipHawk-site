from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from arbitrage_bot import run_arbitrage_scan

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

app = Flask(__name__)
CORS(app)

# Ensure we're in the right directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/script.js')
def serve_js():
    response = send_from_directory(BASE_DIR, 'script.js')
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/styles.css')
def serve_css():
    response = send_from_directory(BASE_DIR, 'styles.css')
    response.headers['Content-Type'] = 'text/css'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(BASE_DIR, 'static')
    return send_from_directory(static_dir, filename)

@app.route('/api/v1/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/scan', methods=['POST'])
def run_scan():
    """Enhanced scan endpoint for real-time resale opportunity detection."""
    try:
        data = request.get_json()
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        
        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required"}), 400
        
        logger.info(f"Running scan for category: {category}, subcategories: {subcategories}")
        
        # Run the real-time arbitrage scan
        start_time = datetime.now()
        results = run_arbitrage_scan(subcategories)
        end_time = datetime.now()
        
        scan_duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan completed in {scan_duration:.2f} seconds with {len(results)} results")
        
        # Process results to include all necessary data
        processed_results = []
        for result in results:
            # Calculate additional metrics
            estimated_tax = result['buyPrice'] * 0.08
            estimated_shipping = determine_shipping_cost(result)
            ebay_fee = calculate_ebay_fee(result['sellPrice'])
            paypal_fee = result['sellPrice'] * 0.029 + 0.30
            
            total_cost = result['buyPrice'] + estimated_tax + estimated_shipping
            total_fees = ebay_fee + paypal_fee
            net_profit = result['sellPrice'] - total_cost - total_fees
            net_profit_percentage = (net_profit / total_cost) * 100 if total_cost > 0 else 0
            
            processed_result = {
                **result,
                'estimatedTax': round(estimated_tax, 2),
                'estimatedShipping': round(estimated_shipping, 2),
                'ebayFee': round(ebay_fee, 2),
                'paypalFee': round(paypal_fee, 2),
                'totalCost': round(total_cost, 2),
                'totalFees': round(total_fees, 2),
                'netProfit': round(net_profit, 2),
                'netProfitPercentage': round(net_profit_percentage, 2),
                'scanDuration': scan_duration
            }
            
            processed_results.append(processed_result)
        
        return jsonify(processed_results)
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}")
        return jsonify({"error": str(e)}), 500

def determine_shipping_cost(item):
    """Calculate shipping cost based on item category."""
    category = item.get('subcategory', '')
    price = item.get('buyPrice', 0)
    
    # Base shipping costs by category
    shipping_rates = {
        'default': 5.99,
        'Laptops': 15.99,
        'Gaming Consoles': 12.99,
        'Guitars': 25.99,
        'Monitors': 18.99,
        'Vintage Tech': 12.99,
        'Collectibles': 4.99,
        'Trading Cards': 3.99,
        'Small Electronics': 7.99
    }
    
    # Determine base rate
    base_rate = shipping_rates.get(category, shipping_rates['default'])
    
    # Adjust for item value (insurance)
    if price > 1000:
        base_rate += 10.00
    elif price > 500:
        base_rate += 5.00
    
    return base_rate

def calculate_ebay_fee(sell_price):
    """Calculate eBay selling fees."""
    if sell_price <= 1:
        return 0
    
    # eBay fee structure (simplified)
    if sell_price <= 150:
        return sell_price * 0.105  # 10.5% for low-value items
    elif sell_price <= 1000:
        return 150 * 0.105 + (sell_price - 150) * 0.085  # 8.5% for medium-value
    else:
        return 150 * 0.105 + 850 * 0.085 + (sell_price - 1000) * 0.065  # 6.5% for high-value

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)

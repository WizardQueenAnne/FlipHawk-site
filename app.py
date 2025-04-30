from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import logging
import json
import traceback
from datetime import datetime, timedelta
from models import db, User, PromoCode, SubscriptionTier, PriceHistory, CategoryPerformance, SavedOpportunity
from auth import auth_bp, token_required, record_price_history
from subscription import subscription, init_promo_codes
from analytics import analytics, create_item_identifier
from filters import filters, OpportunityFilter
from risk_assessment import risk, RiskAnalyzer

# Import the marketplace scanner
from marketplace_scanner import run_arbitrage_scan

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fliphawk.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, resources={"*": {"origins": "*"}})

db.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(subscription)
app.register_blueprint(analytics)
app.register_blueprint(filters)
app.register_blueprint(risk)

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
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disconnected"
    })

@app.route('/api/v1/scan', methods=['POST'])
def run_scan():
    """
    Enhanced scan endpoint using the marketplace scanner.
    This endpoint doesn't require authentication for the demo system.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        
        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required"}), 400
        
        logger.info(f"Running scan for category: {category}, subcategories: {subcategories}")
        
        # Run the arbitrage scan
        results = run_arbitrage_scan(subcategories)
        
        if not results:
            logger.warning("No results found or error occurred during scan")
            return jsonify([])
        
        logger.info(f"Scan completed with {len(results)} results")
        
        # Add category to results if not present
        for result in results:
            if 'category' not in result:
                result['category'] = category
        
        return jsonify(results)
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error processing scan: {str(e)}\n{error_details}")
        return jsonify({"error": "Error connecting to scanning service. Please try again later."}), 500

@app.route('/api/v1/save_opportunity', methods=['POST'])
def save_opportunity():
    """Save an opportunity (simplified for demo without authentication)."""
    try:
        data = request.get_json()
        opportunity = data.get('opportunity')
        notes = data.get('notes', '')
        
        if not opportunity:
            return jsonify({"error": "Opportunity data is required"}), 400
        
        # For demo purposes, we'll just return success
        return jsonify({
            "success": True,
            "message": "Opportunity saved successfully",
            "id": "demo-" + str(int(time.time()))
        })
        
    except Exception as e:
        logger.error(f"Error saving opportunity: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/my_opportunities', methods=['GET'])
def get_opportunities():
    """Get user's saved opportunities (simplified for demo)."""
    # For the demo, return an empty list
    return jsonify([])

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get general stats about the system (for demo purposes)."""
    return jsonify({
        "total_scans": 542,
        "success_rate": 87.5,
        "avg_scan_duration": 28.3,
        "most_profitable_category": "Graphics Cards",
        "most_active_marketplace": "eBay",
        "total_opportunities_found": 3428
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

def calculate_ebay_fee(sell_price):
    """Calculate eBay fee based on selling price."""
    if sell_price <= 100:
        return sell_price * 0.105  # 10.5% for most categories
    elif sell_price <= 1000:
        return 10.5 + (sell_price - 100) * 0.08  # 8% for amount over $100
    else:
        return 82.5 + (sell_price - 1000) * 0.06  # 6% for amount over $1000

def determine_shipping_cost(item):
    """Determine shipping cost based on item category."""
    category = item.get('subcategory', '')
    price = item.get('buyPrice', 0)
    
    # Large/heavy items
    if any(word in category for word in ["Laptop", "Monitor", "PC", "Desktop", "Tower"]):
        return 15.99
    # Medium items
    elif any(word in category for word in ["Keyboard", "Headphone", "Router", "SSD", "GPU", "Microphone"]):
        return 8.99
    # Small items
    elif any(word in category for word in ["Card", "RAM", "Memory", "Cable", "Adapter"]):
        return 3.99
    # Default based on price
    elif price < 50:
        return 4.99
    elif price < 100:
        return 6.99
    elif price < 500:
        return 9.99
    else:
        return 14.99

if __name__ == '__main__':
    import time
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    with app.app_context():
        db.create_all()  # Create database tables
        init_promo_codes()  # Initialize the promo codes
    
    logger.info(f"Starting server on port {port}, debug mode: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)

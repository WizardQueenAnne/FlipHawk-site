from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
from arbitrage_bot import run_arbitrage_scan
from models import db, User, PromoCode, SubscriptionTier, PriceHistory, CategoryPerformance
from auth import auth_bp, token_required, record_price_history
from subscription import subscription, init_promo_codes
from analytics import analytics, create_item_identifier
from filters import filters, OpportunityFilter
from risk_assessment import risk, RiskAnalyzer

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

CORS(app)
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
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/scan', methods=['POST'])
@token_required
def run_scan(current_user):
    """Enhanced scan endpoint with subscription limits and advanced features."""
    try:
        # Check if user can scan
        if not current_user.can_scan():
            return jsonify({
                "error": "Daily scan limit reached",
                "message": "Upgrade to Pro for unlimited scans!",
                "scans_used": current_user.daily_scans_used,
                "limit": 5
            }), 403
        
        data = request.get_json()
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        filters_params = data.get('filters', {})
        
        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required"}), 400
        
        logger.info(f"Running scan for user {current_user.username}: {category}, {subcategories}")
        
        # Run the real-time arbitrage scan
        start_time = datetime.now()
        results = run_arbitrage_scan(subcategories)
        end_time = datetime.now()
        
        # Update user's scan count
        current_user.daily_scans_used += 1
        db.session.commit()
        
        scan_duration = (end_time - start_time).total_seconds()
        logger.info(f"Scan completed in {scan_duration:.2f} seconds with {len(results)} results")
        
        # Apply filters if specified
        if filters_params:
            filter_system = OpportunityFilter(current_user)
            results = filter_system.apply_filters(results, filters_params)
        
        # Process results to include all necessary data
        processed_results = []
        risk_analyzer = RiskAnalyzer()
        
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
            
            # Record price history for both buy and sell prices
            item_identifier = create_item_identifier(result['title'])
            record_price_history(item_identifier, result['buyPrice'], 'eBay-Buy', result.get('buyCondition'))
            record_price_history(item_identifier, result['sellPrice'], 'eBay-Sell', result.get('sellCondition'))
            
            # Update category performance
            update_category_performance(category, result['subcategory'], net_profit, net_profit_percentage)
            
            # Perform risk assessment for Pro/Business users
            risk_score = None
            risk_level = None
            if current_user.subscription_tier != SubscriptionTier.FREE.value:
                risk_score, risk_factors = risk_analyzer.calculate_risk_score(result)
                risk_level = 'low' if risk_score < 30 else 'medium' if risk_score < 60 else 'high'
            
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
                'scanDuration': scan_duration,
                'itemIdentifier': item_identifier,
                'riskScore': risk_score,
                'riskLevel': risk_level
            }
            
            processed_results.append(processed_result)
        
        return jsonify(processed_results)
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}", exc_info=True)
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

def update_category_performance(category, subcategory, profit, profit_margin):
    """Update category performance metrics."""
    perf = CategoryPerformance.query.filter_by(
        category=category,
        subcategory=subcategory
    ).first()
    
    if not perf:
        perf = CategoryPerformance(
            category=category,
            subcategory=subcategory,
            total_opportunities=0,
            successful_flips=0,
            average_profit=0.0,
            average_profit_margin=0.0
        )
        db.session.add(perf)
    
    # Update metrics
    perf.total_opportunities += 1
    if profit > 0:
        perf.successful_flips += 1
    
    # Update averages
    total_ops = perf.total_opportunities
    perf.average_profit = ((perf.average_profit * (total_ops - 1)) + profit) / total_ops
    perf.average_profit_margin = ((perf.average_profit_margin * (total_ops - 1)) + profit_margin) / total_ops
    perf.last_updated = datetime.utcnow()
    
    db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug}")
    
    with app.app_context():
        db.create_all()  # Create database tables
        init_promo_codes()  # Initialize the Seaprep promo code
    
    app.run(host="0.0.0.0", port=port, debug=debug)

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime, timedelta
from models import db, User, PromoCode, SubscriptionTier, PriceHistory, CategoryPerformance, SavedOpportunity
from auth import auth_bp, token_required, record_price_history
from subscription import subscription, init_promo_codes
from analytics import analytics, create_item_identifier
from filters import filters, OpportunityFilter
from risk_assessment import risk, RiskAnalyzer

# Import the marketplace scanner - NEW!
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

# Enable CORS for all API routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
    """Enhanced scan endpoint using the new marketplace scanner."""
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
        
        # Run the marketplace arbitrage scan
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
        
        # Process results with additional category metadata
        processed_results = []
        
        for result in results:
            # Record price history for buy and sell items
            buy_title = result.get('buy_title', result.get('title', ''))
            sell_title = result.get('sell_title', result.get('title', ''))
            
            buy_price = result.get('buy_price', 0)
            sell_price = result.get('sell_price', 0)
            
            item_identifier = create_item_identifier(buy_title)
            record_price_history(item_identifier, buy_price, result.get('buy_marketplace', 'Unknown'), result.get('buy_condition'))
            record_price_history(item_identifier, sell_price, result.get('sell_marketplace', 'Unknown'), result.get('sell_condition'))
            
            # Update category performance
            update_category_performance(category, result.get('subcategory', subcategories[0]), 
                                      result.get('net_profit', 0), result.get('net_profit_percentage', 0))
            
            # Add scan metadata
            result['scan_duration'] = scan_duration
            result['scan_timestamp'] = datetime.now().isoformat()
            result['category'] = category
            
            processed_results.append(result)
        
        return jsonify(processed_results)
        
    except Exception as e:
        logger.error(f"Error processing scan: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/scan/bulk', methods=['POST'])
@token_required
def run_bulk_scan(current_user):
    """Bulk scan endpoint for Business users."""
    try:
        # Check if user has business tier
        if current_user.subscription_tier not in [SubscriptionTier.BUSINESS.value, SubscriptionTier.LIFETIME.value]:
            return jsonify({
                "error": "Business tier required",
                "message": "Upgrade to Business to use bulk scanning!"
            }), 403
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        filters_params = data.get('filters', {})
        
        if not keywords:
            return jsonify({"error": "Keywords are required"}), 400
        
        logger.info(f"Running bulk scan for user {current_user.username}: {len(keywords)} keywords")
        
        # Convert each keyword to a subcategory for the marketplace scanner
        # This allows running multiple independent scans
        all_results = []
        for keyword in keywords[:10]:  # Limit to 10 keywords per request
            keyword_results = run_arbitrage_scan([keyword])
            all_results.extend(keyword_results)
        
        # Apply filters if specified
        if filters_params:
            filter_system = OpportunityFilter(current_user)
            all_results = filter_system.apply_filters(all_results, filters_params)
        
        return jsonify(all_results)
        
    except Exception as e:
        logger.error(f"Error processing bulk scan: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/favorites', methods=['POST'])
@token_required
def save_favorite(current_user):
    """Save an item to favorites."""
    data = request.get_json()
    opportunity_data = data.get('opportunity')
    notes = data.get('notes', '')
    
    if not opportunity_data:
        return jsonify({"error": "Opportunity data is required"}), 400
    
    try:
        saved_opportunity = SavedOpportunity(
            user_id=current_user.id,
            opportunity_data=opportunity_data,
            notes=notes
        )
        
        db.session.add(saved_opportunity)
        db.session.commit()
        
        return jsonify({
            "message": "Opportunity saved successfully",
            "id": saved_opportunity.id
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving favorite: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/favorites', methods=['GET'])
@token_required
def get_favorites(current_user):
    """Get user's saved opportunities."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        opportunities = SavedOpportunity.query.filter_by(user_id=current_user.id)\
            .order_by(SavedOpportunity.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'opportunities': [{
                'id': opp.id,
                'opportunity': opp.opportunity_data,
                'notes': opp.notes,
                'created_at': opp.created_at.isoformat()
            } for opp in opportunities.items],
            'total': opportunities.total,
            'pages': opportunities.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/favorites/<int:favorite_id>', methods=['DELETE'])
@token_required
def delete_favorite(current_user, favorite_id):
    """Delete a saved opportunity."""
    try:
        opportunity = SavedOpportunity.query.filter_by(id=favorite_id, user_id=current_user.id).first()
        
        if not opportunity:
            return jsonify({'message': 'Opportunity not found'}), 404
        
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({'message': 'Opportunity deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting favorite: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

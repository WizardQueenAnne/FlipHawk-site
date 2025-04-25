from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import logging
import json
import asyncio
from arbitrage_bot import run_arbitrage_scan
from collections import deque
import gzip
from io import BytesIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fliphawk.log')
    ]
)
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fliphawk.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Initialize extensions
db = SQLAlchemy(app)
cache = Cache(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Models
class ScanLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    subcategories = db.Column(db.JSON, nullable=False)
    results_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_ip = db.Column(db.String(50))
    duration = db.Column(db.Float)
    success = db.Column(db.Boolean, default=True)

class SavedOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))  # Could be session ID or IP for now
    opportunity_data = db.Column(db.JSON, nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

# Initialize database
with app.app_context():
    db.create_all()

# Middleware for gzip compression
@app.after_request
def compress_response(response):
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    if 'gzip' not in accept_encoding.lower():
        return response
    
    if (200 > response.status_code >= 300) or 'Content-Encoding' in response.headers:
        return response
    
    response.direct_passthrough = False
    
    content = BytesIO(response.get_data())
    gzip_buffer = BytesIO()
    
    with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gzip_file:
        gzip_file.write(content.getvalue())
    
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())
    
    return response

# Performance metrics tracker
class MetricsTracker:
    def __init__(self, max_size=1000):
        self.response_times = deque(maxlen=max_size)
        self.error_count = 0
        self.success_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_request(self, duration, success):
        self.response_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_metrics(self):
        return {
            'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            'success_rate': self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'total_requests': self.success_count + self.error_count
        }

metrics = MetricsTracker()

# Static file serving
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(os.getcwd(), 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory(os.getcwd(), 'script.js')

@app.route('/static/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_dir, filename)

# API Endpoints
@app.route('/api/v1/scan', methods=['POST'])
@limiter.limit("10 per minute")
def run_scan_v1():
    """Enhanced scan endpoint with caching and improved error handling."""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        category = data.get('category', '')
        subcategories = data.get('subcategories', [])
        
        if not category or not subcategories:
            return jsonify({"error": "Category and subcategories are required"}), 400
        
        # Create cache key
        cache_key = f"scan:{category}:{'-'.join(sorted(subcategories))}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for key: {cache_key}")
            metrics.cache_hits += 1
            return jsonify(cached_result)
        
        metrics.cache_misses += 1
        logger.info(f"Running scan for category: {category}, subcategories: {subcategories}")
        
        # Run the scan
        results = run_arbitrage_scan(subcategories)
        
        # Process results with enhanced data
        processed_results = []
        for result in results:
            # Calculate comprehensive cost breakdown
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
                'timestamp': datetime.now().isoformat(),
                'scanDuration': (datetime.now() - start_time).total_seconds()
            }
            
            processed_results.append(processed_result)
        
        # Cache the results
        cache.set(cache_key, processed_results, timeout=300)  # 5 minutes cache
        
        # Log the scan
        duration = (datetime.now() - start_time).total_seconds()
        scan_log = ScanLog(
            category=category,
            subcategories=subcategories,
            results_count=len(processed_results),
            user_ip=request.remote_addr,
            duration=duration,
            success=True
        )
        db.session.add(scan_log)
        db.session.commit()
        
        metrics.record_request(duration, True)
        
        return jsonify(processed_results)
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Error processing scan: {str(e)}")
        
        # Log the failed scan
        scan_log = ScanLog(
            category=data.get('category', 'unknown'),
            subcategories=data.get('subcategories', []),
            results_count=0,
            user_ip=request.remote_addr,
            duration=duration,
            success=False
        )
        db.session.add(scan_log)
        db.session.commit()
        
        metrics.record_request(duration, False)
        
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/save_opportunity', methods=['POST'])
@limiter.limit("50 per hour")
def save_opportunity():
    """Save a resale opportunity for later reference."""
    try:
        data = request.get_json()
        user_id = request.remote_addr  # Use IP as temporary user ID
        
        saved_opp = SavedOpportunity(
            user_id=user_id,
            opportunity_data=data.get('opportunity'),
            notes=data.get('notes', '')
        )
        db.session.add(saved_opp)
        db.session.commit()
        
        return jsonify({"success": True, "id": saved_opp.id})
    except Exception as e:
        logger.error(f"Error saving opportunity: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/my_opportunities', methods=['GET'])
def get_my_opportunities():
    """Get saved opportunities for the current user."""
    try:
        user_id = request.remote_addr
        saved_opps = SavedOpportunity.query.filter_by(user_id=user_id).order_by(SavedOpportunity.saved_at.desc()).all()
        
        return jsonify([{
            'id': opp.id,
            'opportunity': opp.opportunity_data,
            'notes': opp.notes,
            'saved_at': opp.saved_at.isoformat()
        } for opp in saved_opps])
    except Exception as e:
        logger.error(f"Error retrieving opportunities: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get application statistics."""
    try:
        total_scans = ScanLog.query.count()
        success_rate = ScanLog.query.filter_by(success=True).count() / total_scans if total_scans > 0 else 0
        avg_duration = db.session.query(db.func.avg(ScanLog.duration)).scalar() or 0
        
        # Top categories
        top_categories = db.session.query(
            ScanLog.category,
            db.func.count(ScanLog.id).label('count')
        ).group_by(ScanLog.category).order_by(db.desc('count')).limit(5).all()
        
        # Recent scans
        recent_scans = ScanLog.query.order_by(ScanLog.timestamp.desc()).limit(10).all()
        
        stats = {
            'total_scans': total_scans,
            'success_rate': round(success_rate * 100, 2),
            'avg_scan_duration': round(avg_duration, 2),
            'top_categories': [{'category': cat, 'count': count} for cat, count in top_categories],
            'recent_scans': [{
                'category': scan.category,
                'subcategories': scan.subcategories,
                'results_count': scan.results_count,
                'timestamp': scan.timestamp.isoformat()
            } for scan in recent_scans],
            'performance_metrics': metrics.get_metrics()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'cache': 'available',
            'metrics': metrics.get_metrics()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Utility functions
def determine_shipping_cost(item):
    """Calculate shipping cost based on item category and characteristics."""
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

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)

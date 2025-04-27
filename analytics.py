from flask import Blueprint, request, jsonify
from models import db, PriceHistory, CategoryPerformance, User, SubscriptionTier
from auth import token_required
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy import func

analytics = Blueprint('analytics', __name__)

@analytics.route('/api/v1/analytics/price-trends/<item_identifier>', methods=['GET'])
def get_price_trends(item_identifier):
    """Get historical price trends for an item."""
    days = request.args.get('days', 30, type=int)
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    history = PriceHistory.query.filter(
        PriceHistory.item_identifier == item_identifier,
        PriceHistory.timestamp >= cutoff_date
    ).order_by(PriceHistory.timestamp.asc()).all()
    
    # Calculate moving averages and trends
    prices = [h.price for h in history]
    timestamps = [h.timestamp for h in history]
    
    if len(prices) > 7:
        # 7-day moving average
        ma7 = pd.Series(prices).rolling(window=7).mean().tolist()
        
        # Calculate trend (linear regression)
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        trend_line = slope * x + intercept
        
        trend_direction = 'upward' if slope > 0 else 'downward' if slope < 0 else 'stable'
    else:
        ma7 = prices
        trend_line = prices
        trend_direction = 'insufficient_data'
    
    # Compare current price to historical average
    if prices:
        avg_price = np.mean(prices)
        current_price = prices[-1]
        price_vs_average = ((current_price - avg_price) / avg_price) * 100
    else:
        avg_price = 0
        current_price = 0
        price_vs_average = 0
    
    return jsonify({
        'historical_data': [{
            'price': h.price,
            'source': h.source,
            'timestamp': h.timestamp.isoformat(),
            'condition': h.condition
        } for h in history],
        'moving_average_7day': ma7,
        'trend_line': trend_line,
        'trend_direction': trend_direction,
        'average_price': avg_price,
        'current_price': current_price,
        'price_vs_average_percent': price_vs_average
    })

@analytics.route('/api/v1/analytics/category-heatmap', methods=['GET'])
@token_required
def get_category_heatmap(current_user):
    """Get heatmap data for category performance (Pro/Business feature)."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access heatmap analytics'}), 403
    
    # Get category performance data
    performance_data = CategoryPerformance.query.all()
    
    heatmap_data = {}
    for perf in performance_data:
        if perf.category not in heatmap_data:
            heatmap_data[perf.category] = {}
        
        heatmap_data[perf.category][perf.subcategory] = {
            'total_opportunities': perf.total_opportunities,
            'success_rate': (perf.successful_flips / perf.total_opportunities * 100) if perf.total_opportunities > 0 else 0,
            'average_profit': perf.average_profit,
            'average_profit_margin': perf.average_profit_margin,
            'performance_score': calculate_performance_score(perf)
        }
    
    return jsonify(heatmap_data)

def calculate_performance_score(perf):
    """Calculate a performance score for a category/subcategory."""
    # Weight different factors
    success_weight = 0.3
    profit_weight = 0.4
    margin_weight = 0.3
    
    success_rate = (perf.successful_flips / perf.total_opportunities) if perf.total_opportunities > 0 else 0
    
    # Normalize values
    normalized_profit = min(perf.average_profit / 100, 1)  # Cap at $100
    normalized_margin = min(perf.average_profit_margin / 50, 1)  # Cap at 50%
    
    score = (success_rate * success_weight + 
             normalized_profit * profit_weight + 
             normalized_margin * margin_weight) * 100
    
    return round(score, 2)

@analytics.route('/api/v1/analytics/historical-comparison', methods=['GET'])
@token_required
def historical_comparison(current_user):
    """Compare current prices against historical averages (Pro/Business feature)."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access historical comparisons'}), 403
    
    # Get recent scans from the user
    recent_opportunities = current_user.saved_opportunities[-10:]  # Last 10 saved opportunities
    
    comparisons = []
    for opp in recent_opportunities:
        item_identifier = create_item_identifier(opp.opportunity_data.get('title', ''))
        
        # Get historical average for this item
        avg_price_data = db.session.query(
            func.avg(PriceHistory.price).label('avg_price'),
            func.min(PriceHistory.price).label('min_price'),
            func.max(PriceHistory.price).label('max_price'),
            func.count(PriceHistory.id).label('data_points')
        ).filter(PriceHistory.item_identifier == item_identifier).first()
        
        if avg_price_data and avg_price_data.data_points > 5:
            current_price = opp.opportunity_data.get('buyPrice', 0)
            price_vs_avg = ((current_price - avg_price_data.avg_price) / avg_price_data.avg_price) * 100
            
            comparisons.append({
                'title': opp.opportunity_data.get('title'),
                'current_price': current_price,
                'historical_average': avg_price_data.avg_price,
                'historical_min': avg_price_data.min_price,
                'historical_max': avg_price_data.max_price,
                'price_vs_average_percent': price_vs_avg,
                'data_points': avg_price_data.data_points,
                'verdict': 'good_deal' if price_vs_avg < -10 else 'average_deal' if -10 <= price_vs_avg <= 10 else 'expensive'
            })
    
    return jsonify(comparisons)

@analytics.route('/api/v1/analytics/profit-trends', methods=['GET'])
@token_required
def get_profit_trends(current_user):
    """Get profit trends over time (Pro/Business feature)."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access profit trends'}), 403
    
    # Get completed opportunities with actual profit
    completed_flips = SavedOpportunity.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).filter(SavedOpportunity.actual_profit.isnot(None)).all()
    
    # Group by month
    monthly_data = {}
    for flip in completed_flips:
        month_key = flip.created_at.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'total_profit': 0,
                'count': 0,
                'successful': 0
            }
        
        monthly_data[month_key]['total_profit'] += flip.actual_profit
        monthly_data[month_key]['count'] += 1
        if flip.actual_profit > 0:
            monthly_data[month_key]['successful'] += 1
    
    # Calculate monthly statistics
    trends = []
    for month, data in sorted(monthly_data.items()):
        trends.append({
            'month': month,
            'total_profit': data['total_profit'],
            'average_profit': data['total_profit'] / data['count'] if data['count'] > 0 else 0,
            'total_flips': data['count'],
            'success_rate': (data['successful'] / data['count'] * 100) if data['count'] > 0 else 0
        })
    
    return jsonify(trends)

def create_item_identifier(title):
    """Create a unique identifier for an item based on its title."""
    import re
    # Remove special characters and convert to lowercase
    clean_title = re.sub(r'[^a-z0-9\s]', '', title.lower())
    # Extract model numbers or key identifiers
    models = re.findall(r'[a-z0-9]+\d+[a-z0-9]*', clean_title)
    if models:
        return '-'.join(models[:3])  # Use up to 3 model identifiers
    else:
        # Fall back to using key words from title
        words = clean_title.split()
        return '-'.join(words[:5])  # Use first 5 words

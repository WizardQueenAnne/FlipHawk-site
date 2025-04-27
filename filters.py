from flask import Blueprint, request, jsonify
from models import db, User, SubscriptionTier
from auth import token_required

filters = Blueprint('filters', __name__)

class OpportunityFilter:
    """Filter class for applying advanced filters to arbitrage opportunities."""
    
    def __init__(self, user):
        self.user = user
        self.is_pro = user.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.BUSINESS.value, SubscriptionTier.LIFETIME.value]
    
    def apply_filters(self, opportunities, filter_params):
        """Apply all requested filters to opportunities."""
        filtered = opportunities
        
        # Basic filters (available to all users)
        if 'min_profit' in filter_params:
            filtered = [opp for opp in filtered if opp.get('profit', 0) >= filter_params['min_profit']]
        
        if 'max_price' in filter_params:
            filtered = [opp for opp in filtered if opp.get('buyPrice', 0) <= filter_params['max_price']]
        
        # Pro/Business filters
        if self.is_pro:
            if 'min_profit_margin' in filter_params:
                filtered = [opp for opp in filtered if opp.get('profitPercentage', 0) >= filter_params['min_profit_margin']]
            
            if 'conditions' in filter_params and filter_params['conditions']:
                allowed_conditions = filter_params['conditions']
                filtered = [opp for opp in filtered if opp.get('buyCondition', '').lower() in [c.lower() for c in allowed_conditions]]
            
            if 'locations' in filter_params and filter_params['locations']:
                allowed_locations = filter_params['locations']
                filtered = [opp for opp in filtered if opp.get('buyLocation', '') in allowed_locations]
            
            if 'min_confidence' in filter_params:
                filtered = [opp for opp in filtered if opp.get('confidence', 0) >= filter_params['min_confidence']]
            
            if 'min_seller_rating' in filter_params:
                filtered = [opp for opp in filtered if opp.get('sellerRating', 0) >= filter_params['min_seller_rating']]
            
            if 'max_shipping_days' in filter_params:
                filtered = [opp for opp in filtered if opp.get('estimatedShippingDays', 99) <= filter_params['max_shipping_days']]
            
            if 'risk_level' in filter_params:
                allowed_risk = filter_params['risk_level']
                filtered = [opp for opp in filtered if opp.get('riskLevel', 'medium').lower() in [r.lower() for r in allowed_risk]]
        
        return filtered

@filters.route('/api/v1/filters/available', methods=['GET'])
@token_required
def get_available_filters(current_user):
    """Get available filters based on user's subscription tier."""
    base_filters = {
        'min_profit': {
            'type': 'number',
            'description': 'Minimum profit amount',
            'default': 0
        },
        'max_price': {
            'type': 'number',
            'description': 'Maximum buy price',
            'default': 10000
        }
    }
    
    pro_filters = {
        'min_profit_margin': {
            'type': 'number',
            'description': 'Minimum profit margin percentage',
            'default': 20
        },
        'conditions': {
            'type': 'multiselect',
            'options': ['New', 'Like New', 'Very Good', 'Good', 'Acceptable'],
            'description': 'Item condition filter'
        },
        'locations': {
            'type': 'multiselect',
            'options': ['United States', 'Canada', 'United Kingdom', 'Europe', 'Asia'],
            'description': 'Seller location filter'
        },
        'min_confidence': {
            'type': 'number',
            'description': 'Minimum confidence score',
            'default': 70
        },
        'min_seller_rating': {
            'type': 'number',
            'description': 'Minimum seller rating',
            'default': 90
        },
        'max_shipping_days': {
            'type': 'number',
            'description': 'Maximum shipping time in days',
            'default': 7
        },
        'risk_level': {
            'type': 'multiselect',
            'options': ['low', 'medium', 'high'],
            'description': 'Acceptable risk levels'
        }
    }
    
    if current_user.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.BUSINESS.value, SubscriptionTier.LIFETIME.value]:
        return jsonify({**base_filters, **pro_filters})
    else:
        return jsonify(base_filters)

@filters.route('/api/v1/filters/saved', methods=['GET'])
@token_required
def get_saved_filters(current_user):
    """Get user's saved filter presets."""
    # TODO: Implement saved filter presets in database
    return jsonify({
        'presets': [
            {
                'name': 'High Profit Electronics',
                'filters': {
                    'min_profit': 50,
                    'min_profit_margin': 30,
                    'conditions': ['New', 'Like New'],
                    'min_confidence': 80
                }
            },
            {
                'name': 'Low Risk Quick Flips',
                'filters': {
                    'max_price': 100,
                    'min_profit_margin': 25,
                    'risk_level': ['low'],
                    'max_shipping_days': 5
                }
            }
        ]
    })

@filters.route('/api/v1/filters/save', methods=['POST'])
@token_required
def save_filter_preset(current_user):
    """Save a filter preset."""
    data = request.get_json()
    name = data.get('name

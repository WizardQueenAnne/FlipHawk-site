from flask import Blueprint, request, jsonify
from models import db, RiskAssessment, SellerRating, User, SubscriptionTier
from auth import token_required
from datetime import datetime
import numpy as np

risk = Blueprint('risk', __name__)

class RiskAnalyzer:
    """Analyze risk factors for arbitrage opportunities."""
    
    def calculate_risk_score(self, opportunity):
        """Calculate overall risk score (0-100)."""
        factors = {
            'seller_reliability': self.assess_seller_reliability(opportunity),
            'price_volatility': self.assess_price_volatility(opportunity),
            'market_competition': self.assess_market_competition(opportunity),
            'condition_risk': self.assess_condition_risk(opportunity),
            'shipping_risk': self.assess_shipping_risk(opportunity),
            'fraud_probability': self.assess_fraud_probability(opportunity)
        }
        
        # Weight different factors
        weights = {
            'seller_reliability': 0.25,
            'price_volatility': 0.20,
            'market_competition': 0.15,
            'condition_risk': 0.15,
            'shipping_risk': 0.15,
            'fraud_probability': 0.10
        }
        
        risk_score = sum(factors[k] * weights[k] for k in factors)
        return round(risk_score, 2), factors
    
    def assess_seller_reliability(self, opportunity):
        """Assess seller reliability (0-100, lower is better)."""
        seller_id = opportunity.get('seller_id')
        if not seller_id:
            return 50  # Default medium risk
        
        seller_rating = SellerRating.query.filter_by(seller_identifier=seller_id).first()
        
        if not seller_rating:
            return 70  # Higher risk for unknown sellers
        
        # Calculate risk based on rating and feedback
        rating_risk = (100 - seller_rating.positive_feedback_percent) if seller_rating.positive_feedback_percent else 50
        review_count_factor = min(1, seller_rating.total_reviews / 100)  # More reviews = lower risk
        
        return rating_risk * (1 - review_count_factor * 0.5)
    
    def assess_price_volatility(self, opportunity):
        """Assess price volatility risk (0-100, lower is better)."""
        # TODO: Implement price volatility analysis using historical data
        return 30  # Placeholder
    
    def assess_market_competition(self, opportunity):
        """Assess market competition risk (0-100, lower is better)."""
        # TODO: Implement competition analysis
        return 40  # Placeholder
    
    def assess_condition_risk(self, opportunity):
        """Assess condition-related risk (0-100, lower is better)."""
        condition = opportunity.get('buyCondition', '').lower()
        condition_risks = {
            'new': 10,
            'like new': 20,
            'very good': 40,
            'good': 60,
            'acceptable': 80,
            'for parts': 90
        }
        return condition_risks.get(condition, 50)
    
    def assess_shipping_risk(self, opportunity):
        """Assess shipping-related risk (0-100, lower is better)."""
        shipping_time = opportunity.get('estimatedShippingDays', 7)
        location = opportunity.get('buyLocation', '')
        
        # Base risk on shipping time
        time_risk = min(100, shipping_time * 5)
        
        # Adjust for location
        location_risks = {
            'United States': 0,
            'Canada': 10,
            'United Kingdom': 15,
            'Europe': 20,
            'Asia': 30,
            'Other': 40
        }
        location_risk = location_risks.get(location, 30)
        
        return (time_risk + location_risk) / 2
    
    def assess_fraud_probability(self, opportunity):
        """Assess fraud probability (0-100, lower is better)."""
        # Factors that might indicate fraud
        price = opportunity.get('buyPrice', 0)
        market_price = opportunity.get('marketAverage', price)
        
        if market_price > 0 and price < market_price * 0.5:
            # Price too good to be true
            return 80
        
        seller_rating = opportunity.get('sellerRating', 0)
        if seller_rating < 90 and opportunity.get('totalReviews', 0) < 10:
            # Low rating with few reviews
            return 70
        
        return 20  # Base fraud risk

@risk.route('/api/v1/risk/assess', methods=['POST'])
@token_required
def assess_opportunity_risk(current_user):
    """Assess risk for an arbitrage opportunity."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access risk assessment'}), 403
    
    data = request.get_json()
    opportunity = data.get('opportunity', {})
    
    analyzer = RiskAnalyzer()
    risk_score, factors = analyzer.calculate_risk_score(opportunity)
    
    # Determine risk level
    if risk_score < 30:
        risk_level = 'low'
    elif risk_score < 60:
        risk_level = 'medium'
    else:
        risk_level = 'high'
    
    # Save risk assessment
    assessment = RiskAssessment(
        opportunity_id=opportunity.get('id', str(hash(str(opportunity)))),
        risk_score=risk_score,
        fraud_probability=factors['fraud_probability'],
        seller_reliability_score=100 - factors['seller_reliability'],
        market_volatility_score=factors['price_volatility'],
        competition_level=risk_level,
        risk_factors=factors
    )
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify({
        'risk_score': risk_score,
        'risk_level': risk_level,
        'risk_factors': factors,
        'recommendations': generate_recommendations(risk_level, factors)
    })

def generate_recommendations(risk_level, factors):
    """Generate recommendations based on risk assessment."""
    recommendations = []
    
    if risk_level == 'high':
        recommendations.append("Consider skipping this opportunity due to high risk")
    
    if factors['seller_reliability'] > 70:
        recommendations.append("Verify seller credentials before purchasing")
    
    if factors['condition_risk'] > 60:
        recommendations.append("Request additional photos or condition details")
    
    if factors['shipping_risk'] > 50:
        recommendations.append("Consider shipping insurance for this purchase")
    
    if factors['fraud_probability'] > 50:
        recommendations.append("Use secure payment methods with buyer protection")
    
    return recommendations

@risk.route('/api/v1/risk/seller/<seller_id>', methods=['GET'])
@token_required
def get_seller_risk_profile(current_user, seller_id):
    """Get risk profile for a specific seller."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access seller profiles'}), 403
    
    seller_rating = SellerRating.query.filter_by(seller_identifier=seller_id).first()
    
    if not seller_rating:
        return jsonify({'message': 'Seller not found'}), 404
    
    # Calculate seller risk metrics
    analyzer = RiskAnalyzer()
    reliability_score = 100 - analyzer.assess_seller_reliability({'seller_id': seller_id})
    
    return jsonify({
        'seller_id': seller_id,
        'platform': seller_rating.platform,
        'rating': seller_rating.rating,
        'total_reviews': seller_rating.total_reviews,
        'positive_feedback_percent': seller_rating.positive_feedback_percent,
        'return_policy': seller_rating.return_policy,
        'shipping_speed_days': seller_rating.shipping_speed_days,
        'reliability_score': reliability_score,
        'risk_level': 'low' if reliability_score > 80 else 'medium' if reliability_score > 60 else 'high'
    })

@risk.route('/api/v1/risk/batch', methods=['POST'])
@token_required
def batch_risk_assessment(current_user):
    """Perform batch risk assessment for multiple opportunities."""
    if current_user.subscription_tier != SubscriptionTier.BUSINESS.value:
        return jsonify({'message': 'Batch assessment is a Business tier feature'}), 403
    
    data = request.get_json()
    opportunities = data.get('opportunities', [])
    
    analyzer = RiskAnalyzer()
    results = []
    
    for opportunity in opportunities:
        risk_score, factors = analyzer.calculate_risk_score(opportunity)
        risk_level = 'low' if risk_score < 30 else 'medium' if risk_score < 60 else 'high'
        
        results.append({
            'opportunity_id': opportunity.get('id'),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': factors
        })
    
    return jsonify({
        'batch_results': results,
        'summary': {
            'total_assessed': len(results),
            'low_risk': len([r for r in results if r['risk_level'] == 'low']),
            'medium_risk': len([r for r in results if r['risk_level'] == 'medium']),
            'high_risk': len([r for r in results if r['risk_level'] == 'high']),
            'average_risk_score': np.mean([r['risk_score'] for r in results])
        }
    })

@risk.route('/api/v1/risk/return-policy-analysis', methods=['POST'])
@token_required
def analyze_return_policy(current_user):
    """Analyze return policy differences between platforms."""
    if current_user.subscription_tier == SubscriptionTier.FREE.value:
        return jsonify({'message': 'Upgrade to Pro to access return policy analysis'}), 403
    
    data = request.get_json()
    buy_platform = data.get('buy_platform', 'eBay')
    sell_platform = data.get('sell_platform', 'eBay')
    
    # Return policy database (simplified)
    policies = {
        'eBay': {
            'buyer_protection_days': 30,
            'seller_return_acceptance': 'Optional',
            'return_shipping_cost': 'Varies by seller',
            'refund_method': 'Original payment method'
        },
        'Amazon': {
            'buyer_protection_days': 30,
            'seller_return_acceptance': 'Required',
            'return_shipping_cost': 'Free for most items',
            'refund_method': 'Original payment method'
        },
        'Mercari': {
            'buyer_protection_days': 3,
            'seller_return_acceptance': 'Required if item not as described',
            'return_shipping_cost': 'Buyer pays unless item not as described',
            'refund_method': 'Mercari credits or original payment'
        }
    }
    
    buy_policy = policies.get(buy_platform, {})
    sell_policy = policies.get(sell_platform, {})
    
    # Risk analysis based on policy differences
    risk_factors = []
    if buy_policy.get('buyer_protection_days', 0) < sell_policy.get('buyer_protection_days', 0):
        risk_factors.append("Shorter buyer protection period on purchase platform")
    
    if buy_policy.get('return_shipping_cost') == 'Buyer pays':
        risk_factors.append("You may need to pay return shipping if item is defective")
    
    return jsonify({
        'buy_platform_policy': buy_policy,
        'sell_platform_policy': sell_policy,
        'risk_factors': risk_factors,
        'overall_risk': 'high' if len(risk_factors) > 2 else 'medium' if len(risk_factors) > 0 else 'low'
    })

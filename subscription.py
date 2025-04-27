from flask import Blueprint, request, jsonify
from models import db, User, PromoCode, SubscriptionTier
from datetime import datetime, timedelta
from auth import token_required
import os

subscription = Blueprint('subscription', __name__)

# Initialize the Seaprep promo code
def init_promo_codes():
    # Check for Seaprep code
    seaprep_code = PromoCode.query.filter_by(code='SEAPREP').first()
    if not seaprep_code:
        seaprep_code = PromoCode(
            code='SEAPREP',
            subscription_tier=SubscriptionTier.LIFETIME.value,
            duration_days=None,  # Lifetime access
            max_uses=None,  # Unlimited uses
            is_active=True
        )
        db.session.add(seaprep_code)
        db.session.commit()

@subscription.route('/api/v1/subscription/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans."""
    plans = {
        'free': {
            'name': 'Free',
            'price': 0,
            'scans_per_day': 5,
            'features': [
                '5 scans per day',
                'Basic filters',
                'Limited price history',
                'Standard support'
            ]
        },
        'pro': {
            'name': 'Pro',
            'price': 9.99,
            'scans_per_day': 'Unlimited',
            'features': [
                'Unlimited scans',
                'Advanced filters',
                'Full price history',
                'Risk assessment',
                'Deal velocity score',
                'Sell date prediction',
                'Smart price suggestions',
                'Priority support'
            ]
        },
        'business': {
            'name': 'Business',
            'price': 29.99,
            'scans_per_day': 'Unlimited',
            'features': [
                'Everything in Pro',
                'Bulk scanner',
                'API access',
                'Export capabilities',
                'Advanced analytics',
                'Team management',
                'Dedicated support'
            ]
        }
    }
    return jsonify(plans)

@subscription.route('/api/v1/subscription/redeem', methods=['POST'])
@token_required
def redeem_promo_code(current_user):
    """Redeem a promo code."""
    data = request.get_json()
    code = data.get('code', '').upper()
    
    # Special handling for SEAPREP code (case insensitive)
    if code.upper() == 'SEAPREP':
        current_user.subscription_tier = SubscriptionTier.LIFETIME.value
        current_user.subscription_end_date = None  # Lifetime access
        db.session.commit()
        
        return jsonify({
            'message': 'Successfully redeemed SEAPREP code for Lifetime Ultra access!',
            'subscription_tier': current_user.subscription_tier,
            'expires_at': None
        })
    
    # For other promo codes
    promo = PromoCode.query.filter_by(code=code).first()
    
    if not promo or not promo.is_active:
        return jsonify({'message': 'Invalid promo code'}), 400
    
    if promo.expires_at and promo.expires_at < datetime.utcnow():
        return jsonify({'message': 'Promo code has expired'}), 400
    
    if promo.max_uses and promo.times_used >= promo.max_uses:
        return jsonify({'message': 'Promo code has reached maximum uses'}), 400
    
    # Apply promo code
    current_user.subscription_tier = promo.subscription_tier
    if promo.duration_days:
        current_user.subscription_end_date = datetime.utcnow() + timedelta(days=promo.duration_days)
    else:
        current_user.subscription_end_date = None  # Lifetime access
    
    promo.times_used += 1
    db.session.commit()
    
    return jsonify({
        'message': f'Successfully redeemed code for {promo.subscription_tier} tier',
        'subscription_tier': current_user.subscription_tier,
        'expires_at': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None
    })

@subscription.route('/api/v1/subscription/current', methods=['GET'])
@token_required
def get_current_subscription(current_user):
    """Get user's current subscription status."""
    tier_display = current_user.subscription_tier
    if tier_display == 'lifetime':
        tier_display = 'Ultra (Lifetime)'
    elif tier_display == 'pro':
        tier_display = 'Pro'
    elif tier_display == 'business':
        tier_display = 'Business'
    
    return jsonify({
        'subscription_tier': current_user.subscription_tier,
        'tier_display': tier_display,
        'expires_at': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
        'daily_scans_used': current_user.daily_scans_used,
        'scans_remaining': 'Unlimited' if current_user.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.BUSINESS.value, SubscriptionTier.LIFETIME.value] else 5 - current_user.daily_scans_used,
        'can_scan': current_user.can_scan()
    })

@subscription.route('/api/v1/subscription/upgrade', methods=['POST'])
@token_required
def upgrade_subscription(current_user):
    """Upgrade subscription tier (stub for payment integration)."""
    data = request.get_json()
    new_tier = data.get('tier')
    
    valid_tiers = ['free', 'pro', 'business']
    if new_tier not in valid_tiers:
        return jsonify({'message': 'Invalid subscription tier'}), 400
    
    # Don't allow downgrading from lifetime
    if current_user.subscription_tier == SubscriptionTier.LIFETIME.value:
        return jsonify({'message': 'Cannot change from lifetime subscription'}), 400
    
    # TODO: Integrate with payment provider (Stripe/PayPal)
    # For now, just simulate the upgrade
    current_user.subscription_tier = new_tier
    if new_tier != 'free':
        current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    else:
        current_user.subscription_end_date = None
    
    db.session.commit()
    
    tier_name = 'Pro' if new_tier == 'pro' else 'Business' if new_tier == 'business' else 'Free'
    
    return jsonify({
        'message': f'Successfully upgraded to {tier_name} tier',
        'subscription_tier': current_user.subscription_tier,
        'expires_at': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None
    })

@subscription.route('/api/v1/subscription/check-limit', methods=['GET'])
@token_required
def check_scan_limit(current_user):
    """Check if user has reached their scan limit."""
    can_scan = current_user.can_scan()
    
    if not can_scan:
        message = ''
        if current_user.subscription_tier == SubscriptionTier.FREE.value:
            message = 'Daily scan limit reached. Upgrade to Pro for unlimited scans!'
        elif current_user.subscription_tier == SubscriptionTier.PRO.value:
            message = 'Subscription expired. Please renew to continue scanning.'
        
        return jsonify({
            'can_scan': False,
            'message': message,
            'scans_used': current_user.daily_scans_used,
            'limit': 5 if current_user.subscription_tier == SubscriptionTier.FREE.value else 0
        }), 403
    
    return jsonify({
        'can_scan': True,
        'scans_remaining': 'Unlimited' if current_user.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.BUSINESS.value, SubscriptionTier.LIFETIME.value] else 5 - current_user.daily_scans_used
    })

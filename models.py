from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class SubscriptionTier(Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    LIFETIME = "lifetime"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_tier = db.Column(db.String(20), default=SubscriptionTier.FREE.value)
    subscription_end_date = db.Column(db.DateTime)
    daily_scans_used = db.Column(db.Integer, default=0)
    last_scan_reset = db.Column(db.Date, default=datetime.utcnow().date)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_scan(self):
        # Reset daily scan count if it's a new day
        today = datetime.utcnow().date()
        if self.last_scan_reset < today:
            self.daily_scans_used = 0
            self.last_scan_reset = today
            db.session.commit()
        
        # Check scan limits based on subscription
        if self.subscription_tier == SubscriptionTier.FREE.value:
            return self.daily_scans_used < 5
        elif self.subscription_tier == SubscriptionTier.LIFETIME.value:
            return True
        elif self.subscription_tier in [SubscriptionTier.PRO.value, SubscriptionTier.BUSINESS.value]:
            # Check if subscription is still active
            if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
                return True
            return self.daily_scans_used < 5  # Fallback to free tier if expired
        return False

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_identifier = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    condition = db.Column(db.String(50))
    location = db.Column(db.String(100))
    
    __table_args__ = (db.Index('idx_item_identifier', 'item_identifier'),)

class CategoryPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    total_opportunities = db.Column(db.Integer, default=0)
    successful_flips = db.Column(db.Integer, default=0)
    average_profit = db.Column(db.Float, default=0.0)
    average_profit_margin = db.Column(db.Float, default=0.0)
    average_velocity_score = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class SavedOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opportunity_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    actual_profit = db.Column(db.Float)
    is_favorite = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('saved_opportunities', lazy=True))

class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    subscription_tier = db.Column(db.String(20), nullable=False)
    duration_days = db.Column(db.Integer)  # None for lifetime access
    max_uses = db.Column(db.Integer)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_identifier = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'item_identifier', name='_user_item_uc'),)

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    subcategories = db.Column(db.JSON, nullable=False)
    filters = db.Column(db.JSON)
    results_count = db.Column(db.Integer, default=0)
    scan_duration = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('scan_history', lazy=True))

class AuthenticityFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_identifier = db.Column(db.String(256), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    reasons = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_authenticity_item', 'item_identifier'),)

class VelocityMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_identifier = db.Column(db.String(256), nullable=False)
    velocity_score = db.Column(db.Float, nullable=False)
    estimated_sell_days = db.Column(db.Integer)
    sales_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_velocity_item', 'item_identifier'),)

# Add the missing RiskAssessment model class
class RiskAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.String(256), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    fraud_probability = db.Column(db.Float, default=0.0)
    seller_reliability_score = db.Column(db.Float, default=0.0)
    market_volatility_score = db.Column(db.Float, default=0.0)
    competition_level = db.Column(db.String(20), default='medium')
    risk_factors = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_risk_opportunity', 'opportunity_id'),)

# Add the missing SellerRating model class
class SellerRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_identifier = db.Column(db.String(100), nullable=False, unique=True)
    platform = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float)
    total_reviews = db.Column(db.Integer, default=0)
    positive_feedback_percent = db.Column(db.Float)
    return_policy = db.Column(db.String(100))
    shipping_speed_days = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.Index('idx_seller_identifier', 'seller_identifier'),)

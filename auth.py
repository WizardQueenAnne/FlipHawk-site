from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)
db = SQLAlchemy()

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_tier = db.Column(db.String(20), default='free')
    subscription_end_date = db.Column(db.DateTime)
    daily_scans_used = db.Column(db.Integer, default=0)
    last_scan_reset = db.Column(db.Date, default=datetime.utcnow().date)
    
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
        if self.subscription_tier == 'free':
            return self.daily_scans_used < 5
        elif self.subscription_tier in ['pro', 'business', 'lifetime']:
            # Check if subscription is still active
            if self.subscription_tier != 'lifetime' and self.subscription_end_date:
                if self.subscription_end_date < datetime.utcnow():
                    # Subscription expired
                    self.subscription_tier = 'free'
                    db.session.commit()
                    return self.daily_scans_used < 5
            return True
        return False

# Saved opportunities model
class SavedOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opportunity_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    user = db.relationship('User', backref=db.backref('saved_opportunities', lazy=True))

# Price history model
class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_identifier = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    condition = db.Column(db.String(50))
    
    __table_args__ = (db.Index('idx_item_identifier', 'item_identifier'),)

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': 'Token validation failed'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@auth_bp.route('/api/v1/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        if len(data['username']) < 3:
            return jsonify({'message': 'Username must be at least 3 characters long'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already taken'}), 400
        
        user = User(
            email=data['email'],
            username=data['username']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@auth_bp.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            # Token valid for 7 days
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=7)
            }, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithm="HS256")
            
            return jsonify({
                'token': token,
                'username': user.username,
                'email': user.email,
                'subscription_tier': user.subscription_tier
            }), 200
        
        return jsonify({'message': 'Invalid email or password'}), 401
    
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@auth_bp.route('/api/v1/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'subscription_tier': current_user.subscription_tier,
        'subscription_expires': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
        'created_at': current_user.created_at.isoformat()
    }), 200

@auth_bp.route('/api/v1/auth/update-profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        
        if 'username' in data:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'message': 'Username already taken'}), 400
            current_user.username = data['username']
        
        if 'password' in data:
            if len(data['password']) < 6:
                return jsonify({'message': 'Password must be at least 6 characters long'}), 400
            current_user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update profile', 'error': str(e)}), 500

@auth_bp.route('/api/v1/opportunities/save', methods=['POST'])
@token_required
def save_opportunity(current_user):
    try:
        data = request.get_json()
        
        if not data or not data.get('opportunity'):
            return jsonify({'message': 'Missing opportunity data'}), 400
        
        saved_opportunity = SavedOpportunity(
            user_id=current_user.id,
            opportunity_data=data['opportunity'],
            notes=data.get('notes', '')
        )
        
        db.session.add(saved_opportunity)
        db.session.commit()
        
        return jsonify({
            'message': 'Opportunity saved successfully',
            'id': saved_opportunity.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to save opportunity', 'error': str(e)}), 500

@auth_bp.route('/api/v1/opportunities/saved', methods=['GET'])
@token_required
def get_saved_opportunities(current_user):
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
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch saved opportunities', 'error': str(e)}), 500

@auth_bp.route('/api/v1/opportunities/saved/<int:id>', methods=['DELETE'])
@token_required
def delete_saved_opportunity(current_user, id):
    try:
        opportunity = SavedOpportunity.query.filter_by(id=id, user_id=current_user.id).first()
        
        if not opportunity:
            return jsonify({'message': 'Opportunity not found'}), 404
        
        db.session.delete(opportunity)
        db.session.commit()
        
        return jsonify({'message': 'Opportunity deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete opportunity', 'error': str(e)}), 500

@auth_bp.route('/api/v1/price-history/<item_identifier>', methods=['GET'])
def get_price_history(item_identifier):
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        history = PriceHistory.query.filter(
            PriceHistory.item_identifier == item_identifier,
            PriceHistory.timestamp >= cutoff_date
        ).order_by(PriceHistory.timestamp.asc()).all()
        
        return jsonify([{
            'price': h.price,
            'source': h.source,
            'timestamp': h.timestamp.isoformat(),
            'condition': h.condition
        } for h in history]), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch price history', 'error': str(e)}), 500

# Function to record price history
def record_price_history(item_identifier, price, source, condition=None):
    try:
        price_record = PriceHistory(
            item_identifier=item_identifier,
            price=price,
            source=source,
            condition=condition
        )
        db.session.add(price_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

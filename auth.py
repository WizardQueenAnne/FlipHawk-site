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
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@auth_bp.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'message': 'Missing required fields'}), 400
    
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

@auth_bp.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
        }, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithm="HS256")
        
        return jsonify({
            'token': token,
            'username': user.username,
            'email': user.email
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@auth_bp.route('/api/v1/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'is_premium': current_user.is_premium,
        'created_at': current_user.created_at.isoformat()
    }), 200

@auth_bp.route('/api/v1/opportunities/save', methods=['POST'])
@token_required
def save_opportunity(current_user):
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

@auth_bp.route('/api/v1/opportunities/saved', methods=['GET'])
@token_required
def get_saved_opportunities(current_user):
    opportunities = SavedOpportunity.query.filter_by(user_id=current_user.id)\
        .order_by(SavedOpportunity.created_at.desc()).all()
    
    return jsonify([{
        'id': opp.id,
        'opportunity': opp.opportunity_data,
        'notes': opp.notes,
        'created_at': opp.created_at.isoformat()
    } for opp in opportunities]), 200

@auth_bp.route('/api/v1/price-history/<item_identifier>', methods=['GET'])
def get_price_history(item_identifier):
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

# Function to record price history
def record_price_history(item_identifier, price, source, condition=None):
    price_record = PriceHistory(
        item_identifier=item_identifier,
        price=price,
        source=source,
        condition=condition
    )
    db.session.add(price_record)
    db.session.commit()id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Saved opportunities model
class SavedOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opportunity_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

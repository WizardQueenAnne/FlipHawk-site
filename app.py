from flask import Flask, send_from_directory, request, jsonify, session
import os
from arbitrage_bot import run_arbitrage_scan
import json
from datetime import datetime
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Mock user database for demonstration
users_db = {}
favorites_db = {}
feedback_db = []

# Ensure the static directory exists
static_dir = os.path.join(os.getcwd(), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Serve the index.html from the root directory
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

# Serve static files
@app.route('/styles.css')
def serve_css():
    return send_from_directory(os.getcwd(), 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory(os.getcwd(), 'script.js')

# Serve logo images
@app.route('/logo.png')
def serve_logo():
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'logo.png')

@app.route('/mini-logo.png')
def serve_mini_logo():
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'mini-logo.png')

# API endpoint for running the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    data = request.get_json()
    category = data.get('category', '')
    subcategories = data.get('subcategories', [])
    
    if not category or not subcategories:
        return jsonify({"error": "Category and subcategories are required"}), 400
    
    # Run the arbitrage scan with the subcategories as keywords
    result = run_arbitrage_scan(subcategories)
    
    # Log this scan for statistics
    log_scan(category, subcategories, len(result))
    
    return jsonify(result)

# New route for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required"}), 400
    
    if email in users_db:
        return jsonify({"error": "Email already registered"}), 400
    
    # In a real app, you would hash the password
    users_db[email] = {
        "password": password,
        "name": name,
        "joined": datetime.now().isoformat()
    }
    
    # Create empty favorites list for user
    favorites_db[email] = []
    
    # Set session for user
    session['user_email'] = email
    
    return jsonify({
        "success": True,
        "user": {
            "email": email,
            "name": name
        }
    })

# New route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    if email not in users_db or users_db[email]["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Set session for user
    session['user_email'] = email
    
    return jsonify({
        "success": True,
        "user": {
            "email": email,
            "name": users_db[email]["name"]
        }
    })

# New route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({"success": True})

# New route for getting user favorites
@app.route('/favorites', methods=['GET'])
def get_favorites():
    if 'user_email' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    email = session['user_email']
    
    if email not in favorites_db:
        favorites_db[email] = []
    
    return jsonify(favorites_db[email])

# New route for adding to favorites
@app.route('/favorites', methods=['POST'])
def add_favorite():
    if 'user_email' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    email = session['user_email']
    data = request.get_json()
    
    if email not in favorites_db:
        favorites_db[email] = []
    
    # Check if already in favorites
    for fav in favorites_db[email]:
        if fav['buyLink'] == data['buyLink'] and fav['sellLink'] == data['sellLink']:
            return jsonify({"error": "Already in favorites"}), 400
    
    favorites_db[email].append(data)
    
    return jsonify({"success": True})

# New route for removing from favorites
@app.route('/favorites', methods=['DELETE'])
def remove_favorite():
    if 'user_email' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    email = session['user_email']
    data = request.get_json()
    
    if email not in favorites_db:
        return jsonify({"error": "No favorites found"}), 400
    
    # Find and remove the favorite
    for i, fav in enumerate(favorites_db[email]):
        if fav['buyLink'] == data['buyLink'] and fav['sellLink'] == data['sellLink']:
            favorites_db[email].pop(i)
            return jsonify({"success": True})
    
    return jsonify({"error": "Favorite not found"}), 404

# New route for submitting feedback
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    feedback_type = data.get('type')
    message = data.get('message')
    
    if not feedback_type or not message:
        return jsonify({"error": "Feedback type and message are required"}), 400
    
    # Store feedback with user info if logged in
    feedback_entry = {
        "type": feedback_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "user": session.get('user_email', 'anonymous')
    }
    
    feedback_db.append(feedback_entry)
    
    return jsonify({"success": True})

# New route for getting stats
@app.route('/stats', methods=['GET'])
def get_stats():
    # In a real app, these would be calculated from actual data
    scanning_count = len(scan_log) * 20  # Rough estimate
    
    # Count weekly deals from the log
    current_date = datetime.now()
    weekly_deals = 0
    
    for entry in scan_log:
        scan_date = datetime.fromisoformat(entry['timestamp'])
        days_diff = (current_date - scan_date).days
        
        if days_diff <= 7:
            weekly_deals += entry['results_count']
    
    # Count active users (simplified for demo)
    active_users = len(users_db)
    
    return jsonify({
        "scanning_count": scanning_count,
        "weekly_deals": weekly_deals,
        "active_users": active_users
    })

# Logging for scan statistics
scan_log = []

def log_scan(category, subcategories, results_count):
    scan_entry = {
        "category": category,
        "subcategories": subcategories,
        "results_count": results_count,
        "timestamp": datetime.now().isoformat(),
        "user": session.get('user_email', 'anonymous')
    }
    
    scan_log.append(scan_entry)
    
    # In a real app, you would save this to a database

if __name__ == '__main__':
    # Use environment variable to specify the port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

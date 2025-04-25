from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

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

@app.route('/api/v1/health')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/api/v1/scan', methods=['POST'])
def scan():
    # Return dummy data for testing
    return jsonify([
        {
            "title": "Test Product",
            "buyPrice": 50.00,
            "sellPrice": 100.00,
            "profit": 50.00,
            "profitPercentage": 100.0,
            "confidence": 90,
            "buyLink": "https://example.com/buy",
            "sellLink": "https://example.com/sell"
        }
    ])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}")
    print(f"Base directory: {BASE_DIR}")
    print(f"Files in directory: {os.listdir(BASE_DIR)}")
    app.run(host="0.0.0.0", port=port, debug=True)

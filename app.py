from flask import Flask, send_from_directory
import os
from arbitrage_bot import run_arbitrage_scan  # Import your arbitrage bot directly from the root

# Initialize Flask app
app = Flask(__name__)

# Serve the index.html from the root directory
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

# Additional route for running the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    # Trigger your arbitrage scan logic here
    result = run_arbitrage_scan()
    return result  # Return results as needed

if __name__ == '__main__':
    # Use environment variable to specify the port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

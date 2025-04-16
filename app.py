from flask import Flask, send_from_directory
import os
from arbitrage_bot import run_arbitrage_scan  # Assuming you want to import your arbitrage scan function here

# Initialize Flask app
app = Flask(__name__)

# Serve the index.html from the root directory
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

# Additional route for running the arbitrage scan
@app.route('/run_scan', methods=['POST'])
def run_scan():
    # Assuming 'run_arbitrage_scan' is a function from your arbitrage_bot module
    # You can modify the function to accept parameters if needed
    result = run_arbitrage_scan()  # This will trigger your arbitrage logic
    return result  # You can return a JSON response or something more useful here

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template_string
from arbitrage_bot import run_bot
import os

app = Flask(__name__)

@app.route('/')
def index():
    return open('static/index.html').read()

@app.route('/search', methods=['POST'])
def search():
    category = request.json.get('category')
    if not category:
        return jsonify({'error': 'No category provided'}), 400
    deals = run_bot(category)
    return jsonify(deals)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

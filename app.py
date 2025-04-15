from flask import Flask, request, jsonify, render_template
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search')
def search():
    category = request.args.get('category')
    subcategories = request.args.getlist('subcategories')

    if not category or not subcategories:
        return jsonify({'deals': []})
    
    # Example mock data, replace with actual scraping logic
    deals = [
        {'title': 'Headphones', 'price': 50, 'link': 'https://www.example.com/headphones'},
        {'title': 'Smartphone', 'price': 200, 'link': 'https://www.example.com/smartphone'},
    ]

    # Return some mock data for demonstration
    return jsonify({'deals': deals})

if __name__ == "__main__":
    app.run(debug=True)

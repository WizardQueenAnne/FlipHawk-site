from flask import Flask, request, render_template_string, jsonify
from arbitrage_bot import run_arbitrage_scan

app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(open("index.html").read())

@app.route("/run", methods=["POST"])
def run():
    data = request.json
    selected_keywords = data.get("keywords", [])
    if not selected_keywords:
        return jsonify({"error": "No keywords provided"}), 400
    
    print(f"Running arbitrage bot with keywords: {selected_keywords}")
    deals = run_arbitrage_scan(selected_keywords)
    return jsonify(deals)

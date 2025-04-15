from flask import Flask, request, jsonify, send_from_directory
from arbitrage_bot.arbitrage_bot import run_arbitrage_scan
import os

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/run", methods=["POST"])
def run_arbitrage():
    data = request.get_json()

    keywords = data.get("keywords", [])
    if not keywords:
        return jsonify({"error": "No keywords provided."}), 400

    try:
        deals = run_arbitrage_scan(keywords)
        return jsonify(deals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

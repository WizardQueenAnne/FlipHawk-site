from flask import Flask, request, send_from_directory
import subprocess

app = Flask(__name__, static_folder='static')

CATEGORY_KEYWORDS = {
    "trading_cards": ["yugioh", "pokemon", "magic the gathering", "baseball cards", "football cards", "soccer cards"],
    "collectibles": ["funko pop", "lego sets", "coins", "stamps"],
    "antiques": ["vintage clock", "old camera", "antique furniture"],
    "tech": ["laptop", "tablet", "camera", "headphones"]
}

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/start_search")
def start_search():
    category = request.args.get("category")
    keywords = CATEGORY_KEYWORDS.get(category, [])

    if not keywords:
        return "❌ Invalid category selected.", 400

    try:
        result = subprocess.check_output(
            ["python3", "arbitrage_bot/arbitrage_bot.py", *keywords],
            stderr=subprocess.STDOUT,
            timeout=300
        )
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"❌ Bot error:\n{e.output.decode('utf-8')}", 500
    except subprocess.TimeoutExpired:
        return "❌ Search took too long and timed out.", 500

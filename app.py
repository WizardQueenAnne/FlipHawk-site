from flask import Flask, render_template, request
from arbitrage_bot.arbitrage_bot import run_arbitrage_bot
import os

app = Flask(__name__, static_folder="static", template_folder="static")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/run-bot", methods=["POST"])
def run_bot():
    category = request.form.get("category")
    if not category:
        return "No category provided.", 400

    print(f"🔍 Running arbitrage bot for category: {category}")
    deals = run_arbitrage_bot(category)

    return "<br><br>".join(deals)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("✅ Flask app is starting...")
    app.run(host="0.0.0.0", port=port)

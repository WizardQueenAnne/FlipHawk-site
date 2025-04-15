from flask import Flask, request, render_template_string
from arbitrage_bot.arbitrage_bot import run_arbitrage_bot
import os

app = Flask(__name__)

# Load your static index.html manually from the file
with open("static/index.html", "r") as file:
    index_html = file.read()

@app.route("/", methods=["GET"])
def index():
    return render_template_string(index_html)

@app.route("/run-bot", methods=["POST"])
def run_bot():
    category = request.form.get("category")
    try:
        results = run_arbitrage_bot(category)
        output = "<h2>Top Deals:</h2><ul>"
        for deal in results:
            output += f"<li>{deal}</li>"
        output += "</ul><a href='/'>Back</a>"
        return output
    except Exception as e:
        return f"<p>Error: {str(e)}</p><a href='/'>Back</a>"

# ✅ Bind to the correct port for Render deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Fallback for local
    app.run(host="0.0.0.0", port=port)

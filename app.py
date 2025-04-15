from flask import Flask, request, render_template_string
from arbitrage_bot import run_arbitrage_bot

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    deals = []
    if request.method == "POST":
        category = request.form.get("category")
        subcategories = request.form.getlist("subcategories")
        deals = run_arbitrage_bot(category, subcategories)
    return render_template_string(open("index.html").read(), deals=deals)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

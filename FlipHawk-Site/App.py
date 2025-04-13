from flask import Flask, render_template, request
from arbitrage_bot import run_arbitrage_bot

app = Flask(__name__, static_folder="static", template_folder="static")

CATEGORY_KEYWORDS = {
    "Trading Cards": ["pokemon", "magic the gathering", "yugioh", "baseball cards", "football cards", "soccer cards"],
    "Collectibles": ["funko pop", "lego sets", "coins", "action figures"],
    "Antiques": ["vintage", "typewriter", "old clock", "antique jewelry"],
    "Tech": ["laptop", "headphones", "camera", "tablet"]
}

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        category = request.form.get("category")
        keywords = CATEGORY_KEYWORDS.get(category, [])
        results = run_arbitrage_bot(keywords)
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)

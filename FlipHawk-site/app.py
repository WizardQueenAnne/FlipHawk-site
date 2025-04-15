import os
from flask import Flask, request, render_template
from arbitrage_bot.arbitrage_bot import run_arbitrage_bot

app = Flask(__name__, static_folder='static', template_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-bot', methods=['POST'])
def run_bot():
    category = request.form.get('category')
    if not category:
        return "No category provided", 400
    try:
        results = run_arbitrage_bot(category)
        return "<br><br>".join(results) if results else "No good deals found right now."
    except Exception as e:
        return f"Error running bot: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use the PORT provided by Render
    app.run(host="0.0.0.0", port=port)

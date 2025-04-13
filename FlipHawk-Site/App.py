from flask import Flask, request, render_template, jsonify
import os
import subprocess

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/start-search', methods=['POST'])
def start_search():
    data = request.get_json()
    category = data.get('category')

    category_keywords = {
        "trading cards": ["pokemon", "magic the gathering", "yu-gi-oh", "baseball cards", "football cards", "soccer cards"],
        "collectibles": ["funko pop", "lego set", "model cars", "vintage toys"],
        "antiques": ["antique clock", "vintage lamp", "old coin", "typewriter"],
        "tech": ["laptop", "headphones", "tablet", "camera"]
    }

    keywords = category_keywords.get(category.lower(), [])

    if not keywords:
        return jsonify({"status": "error", "message": "Invalid category selected."}), 400

    # Run the bot with keywords passed as arguments
    cmd = ['python', 'arbitrage_bot/arbitrage_bot.py'] + keywords
    try:
        result = subprocess.check_output(cmd, text=True, timeout=120)
        return jsonify({"status": "success", "output": result})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Bot failed: {e.output}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

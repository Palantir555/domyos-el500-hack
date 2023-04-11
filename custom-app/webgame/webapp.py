from flask import Flask, render_template, jsonify
import random
import math

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_data")
def data():
    speed = random.uniform(0, 20)  # Random speed between 0.5 and 3
    resistance = random.uniform(1, 16)  # Random resistance between 0 and 1
    return jsonify({"speed": speed, "resistance": resistance})

def run_app():
    app.run(host="0.0.0.0", debug=True)

if __name__ == "__main__":
    run_app()


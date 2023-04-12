from flask import Flask, render_template, jsonify
import random
import math

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_data")
def data():
    # Ball 0 (user-controlled)
    speed = random.uniform(20, 25)  # Random speed between 10 and 25
    slope = random.uniform(-10, 40)   # Random slope between 0 and 40

    # Generate data for additional balls
    additional_balls = []
    for i in range(1, 4):
        additional_speed = random.uniform(10, 35)
        additional_slope = random.uniform(-10, 40)
        additional_balls.append({"id": i, "speed": additional_speed, "slope": additional_slope})

    all_ball_data = [{"id": 0, "speed": speed, "slope": slope}] + additional_balls
    return jsonify(all_ball_data)

def run_app():
    app.run(host="0.0.0.0", debug=True)

if __name__ == "__main__":
    run_app()


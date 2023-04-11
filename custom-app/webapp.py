from flask import Flask, render_template, jsonify
from threading import Thread
from queue import Queue
import time

app = Flask(__name__)

data_queue = Queue()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_data")
def data():
    if not data_queue.empty():
        data = data_queue.get()
        return jsonify(data)
    else:
        return jsonify({"kmph": None, "resistance": None})


def run_app():
    app.run(host="0.0.0.0", debug=True)


if __name__ == "__main__":
    run_app()


from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)
CONFIG_PATH = "../config.json"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sports = request.form.getlist("sports")
        scroll_speed = int(request.form["scroll_speed"])
        font_size = int(request.form["font_size"])
        refresh_interval = int(request.form["refresh_interval"])

        config = {
            "sports": sports,
            "scroll_speed": scroll_speed,
            "font_size": font_size,
            "refresh_interval": refresh_interval
        }

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        return redirect("/")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    return render_template("index.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)
CONFIG_PATH = "../config.json"

SPORTS_OPTIONS = [
    {"sport": "football", "league": "nfl", "label": "NFL"},
    {"sport": "basketball", "league": "nba", "label": "NBA"},
    {"sport": "baseball", "league": "mlb", "label": "MLB"},
    {"sport": "hockey", "league": "nhl", "label": "NHL"},
]

TIME_ZONES = [
    "America/New_York", "Europe/London", "Asia/Tokyo", "America/Los_Angeles",
    "Australia/Sydney", "Europe/Berlin", "Asia/Dubai", "UTC"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        scroll_speed = int(request.form["scroll_speed"])
        font_size = int(request.form["font_size"])
        refresh_interval = int(request.form["refresh_interval"])
        time_zones = request.form.getlist("time_zones")

        selected_leagues = request.form.getlist("sports")
        sports = []
        for s in SPORTS_OPTIONS:
            if s["league"] in selected_leagues:
                sports.append({"sport": s["sport"], "league": s["league"]})

        config = {
            "sports": sports,
            "scroll_speed": scroll_speed,
            "font_size": font_size,
            "refresh_interval": refresh_interval,
            "time_zones": time_zones
        }

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        return redirect("/")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    selected_leagues = [s["league"] for s in config.get("sports", [])]

    return render_template("index.html",
                           config=config,
                           sports_options=SPORTS_OPTIONS,
                           selected_leagues=selected_leagues,
                           all_zones=TIME_ZONES)

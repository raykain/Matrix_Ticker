import pygame
import requests
import json
import time
from datetime import datetime
import pytz

CONFIG_PATH = "config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def fetch_scores(sport_leagues):
    all_scores = []
    for entry in sport_leagues:
        sport = entry["sport"]
        league = entry["league"]
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
        try:
            response = requests.get(url)
            games = response.json().get("events", [])
            for game in games:
                comps = game['competitions'][0]['competitors']
                team1 = comps[0]['team']['shortDisplayName']
                score1 = comps[0].get('score', '0')
                team2 = comps[1]['team']['shortDisplayName']
                score2 = comps[1].get('score', '0')
                all_scores.append(f"{league.upper()}: {team1} {score1} - {team2} {score2}")
        except Exception as e:
            all_scores.append(f"{league.upper()}: Error loading scores")
    return all_scores or ["No games available"]

def format_clocks(time_zones):
    now = datetime.utcnow()
    clocks = []
    for zone in time_zones:
        tz = pytz.timezone(zone)
        local_time = now.astimezone(tz).strftime('%H:%M:%S')
        label = zone.split('/')[-1].replace('_', ' ')
        clocks.append(f"{label}: {local_time}")
    return "   |   ".join(clocks)

def run_ticker():
    pygame.init()
    screen = pygame.display.set_mode((1920, 360))
    pygame.display.set_caption("Sports Ticker")
    clock = pygame.time.Clock()
    bg_color = (0, 0, 0)
    text_color = (255, 255, 255)

    while True:
        config = load_config()
        font = pygame.font.SysFont("Arial", config["font_size"])
        small_font = pygame.font.SysFont("Arial", 40)

        scores = fetch_scores(config["sports"])
        combined_scores = "     ||     ".join(scores)
        score_surface = font.render(combined_scores, True, text_color)
        score_width = score_surface.get_width()

        x = 1920
        start_time = time.time()

        while time.time() - start_time < config["refresh_interval"]:
            screen.fill(bg_color)

            clock_text = format_clocks(config.get("time_zones", []))
            clock_surface = small_font.render(clock_text, True, text_color)
            screen.blit(clock_surface, (20, 20))

            screen.blit(score_surface, (x, 160))
            x -= config["scroll_speed"]
            if x < -score_width:
                x = 1920

            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    try:
        run_ticker()
    except KeyboardInterrupt:
        pygame.quit()

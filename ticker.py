import pygame
import requests
import json
import time
import os

CONFIG_PATH = "config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def fetch_scores(sports):
    all_scores = []
    for sport in sports:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/{sport}/scoreboard"
        try:
            response = requests.get(url)
            games = response.json().get("events", [])
            for game in games:
                comps = game['competitions'][0]['competitors']
                team1 = comps[0]['team']['shortDisplayName']
                score1 = comps[0].get('score', '0')
                team2 = comps[1]['team']['shortDisplayName']
                score2 = comps[1].get('score', '0')
                all_scores.append(f"{team1} {score1} - {team2} {score2}")
        except Exception as e:
            all_scores.append(f"Error loading {sport.upper()} scores")
    return all_scores or ["No games available"]

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
        messages = fetch_scores(config["sports"])
        combined = "     ||     ".join(messages)
        text_surface = font.render(combined, True, text_color)
        text_width = text_surface.get_width()

        x = 1920
        start_time = time.time()

        while time.time() - start_time < config["refresh_interval"]:
            screen.fill(bg_color)
            screen.blit(text_surface, (x, 100))
            x -= config["scroll_speed"]
            if x < -text_width:
                x = 1920
            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    try:
        run_ticker()
    except KeyboardInterrupt:
        pygame.quit()

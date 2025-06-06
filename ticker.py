import os
os.environ["SDL_VIDEODRIVER"] = "x11"  # Needed for most Raspberry Pi setups with GUI

import pygame
import requests
import json
import time
from datetime import datetime
from io import BytesIO
from PIL import Image
import pytz

CONFIG_PATH = "config.json"
LOGO_DIR = "logos"
os.makedirs(LOGO_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def download_logo(url, team_id):
    path = os.path.join(LOGO_DIR, f"{team_id}.png")
    if not os.path.exists(path):
        try:
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            img = img.resize((80, 80))
            img.save(path)
        except Exception as e:
            print(f"Logo download failed for {team_id}: {e}")
            return None
    return path

def fetch_scores(sport_leagues):
    all_scores = []
    for entry in sport_leagues:
        sport = entry["sport"]
        league = entry["league"]
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
        try:
            response = requests.get(url, timeout=5)
            games = response.json().get("events", [])
            for game in games:
                comps = game['competitions'][0]['competitors']
                t1 = comps[0]
                t2 = comps[1]

                item = {
                    "league": league.upper(),
                    "team1": t1['team']['shortDisplayName'],
                    "team2": t2['team']['shortDisplayName'],
                    "score1": t1.get('score', '0'),
                    "score2": t2.get('score', '0'),
                    "logo1": download_logo(t1['team']['logo'][0]['href'], t1['team']['id']),
                    "logo2": download_logo(t2['team']['logo'][0]['href'], t2['team']['id'])
                }
                all_scores.append(item)
        except Exception as e:
            print(f"Error loading {league.upper()} scores: {e}")
            all_scores.append({
                "league": league.upper(),
                "team1": "Error",
                "team2": "",
                "score1": "",
                "score2": "",
                "logo1": None,
                "logo2": None
            })
    return all_scores

def format_clocks(time_zones):
    now = datetime.utcnow()
    clocks = []
    for zone in time_zones:
        try:
            tz = pytz.timezone(zone)
            local_time = now.astimezone(tz).strftime('%H:%M:%S')
            label = zone.split('/')[-1].replace('_', ' ')
            clocks.append(f"{label}: {local_time}")
        except:
            continue
    return "   |   ".join(clocks)

def render_score_items(scores, font):
    surfaces = []
    for item in scores:
        text = f"{item['team1']} {item['score1']} - {item['score2']} {item['team2']}"
        text_surface = font.render(text, True, (255, 255, 255))
        
        combined_width = 80 + text_surface.get_width() + 80 + 60
        surface = pygame.Surface((combined_width, 80), pygame.SRCALPHA)

        if item['logo1']:
            logo1 = pygame.image.load(item['logo1'])
            surface.blit(logo1, (0, 0))
        surface.blit(text_surface, (90, 20))
        if item['logo2']:
            logo2 = pygame.image.load(item['logo2'])
            surface.blit(logo2, (90 + text_surface.get_width() + 10, 0))

        surfaces.append(surface)
    return surfaces

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
        score_surfaces = render_score_items(scores, font)

        x = 1920
        start_time = time.time()

        while time.time() - start_time < config["refresh_interval"]:
            screen.fill(bg_color)

            clock_text = format_clocks(config.get("time_zones", []))
            clock_surface = small_font.render(clock_text, True, text_color)
            screen.blit(clock_surface, (20, 20))

            offset = x
            for surf in score_surfaces:
                screen.blit(surf, (offset, 160))
                offset += surf.get_width() + 40

            x -= config["scroll_speed"]
            if offset < 0:
                x = 1920

            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    try:
        run_ticker()
    except KeyboardInterrupt:
        pygame.quit()

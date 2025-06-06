import os
os.environ["SDL_VIDEODRIVER"] = "x11"  # For Raspberry Pi GUI mode

import pygame
import requests
import json
import time
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw
import pytz

CONFIG_PATH = "config.json"
LOGO_DIR = "logos"
os.makedirs(LOGO_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def download_logo(url, team_id):
    if not url:
        return None

    # Paths for both sizes
    path_90 = os.path.join(LOGO_DIR, f"{team_id}_90.png")
    path_100 = os.path.join(LOGO_DIR, f"{team_id}_100.png")
    if os.path.exists(path_90) and os.path.exists(path_100):
        return path_90, path_100

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            # Open and resize original logo to 80x80 for best quality inside border
            logo = Image.open(BytesIO(response.content)).convert("RGBA")
            logo = logo.resize((80, 80), Image.LANCZOS)

            # Create circular mask for logo
            mask = Image.new("L", logo.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo.size[0], logo.size[1]), fill=255)
            logo.putalpha(mask)

            # === Create 90x90 image with thin border ===
            size_90 = (90, 90)
            bg_90 = Image.new("RGBA", size_90, (0, 0, 0, 0))
            draw_90 = ImageDraw.Draw(bg_90)
            # Thin white circle border - radius 44, border thickness 2 px
            draw_90.ellipse((1, 1, size_90[0]-2, size_90[1]-2), fill=(255, 255, 255, 255))
            offset_90 = ((size_90[0] - logo.size[0]) // 2, (size_90[1] - logo.size[1]) // 2)
            bg_90.paste(logo, offset_90, logo)
            bg_90.save(path_90)

            # === Create 100x100 image with thicker border ===
            size_100 = (100, 100)
            bg_100 = Image.new("RGBA", size_100, (0, 0, 0, 0))
            draw_100 = ImageDraw.Draw(bg_100)
            # Thick white circle border - radius 48, border thickness 6 px
            # Draw white filled circle
            draw_100.ellipse((0, 0, size_100[0], size_100[1]), fill=(255, 255, 255, 255))
            # Draw smaller black circle inside to create border effect
            inner_margin = 6
            draw_100.ellipse((inner_margin, inner_margin, size_100[0]-inner_margin, size_100[1]-inner_margin), fill=(0, 0, 0, 0))
            # Paste the logo centered inside the transparent circle
            offset_100 = ((size_100[0] - logo.size[0]) // 2, (size_100[1] - logo.size[1]) // 2)
            bg_100.paste(logo, offset_100, logo)
            bg_100.save(path_100)

            return path_90, path_100

    except Exception as e:
        print(f"Error downloading logo for {team_id}: {e}")

    return None, None


def extract_logo_url(team):
    if 'logo' in team:
        return team['logo']
    elif 'logos' in team and isinstance(team['logos'], list) and team['logos']:
        return team['logos'][0].get('href')
    return None

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

                team1_logo_url = extract_logo_url(t1['team'])
                team2_logo_url = extract_logo_url(t2['team'])
                team1_id = t1['team']['id']
                team2_id = t2['team']['id']

                team1_logo_path = download_logo(team1_logo_url, team1_id)
                team2_logo_path = download_logo(team2_logo_url, team2_id)

                item = {
                    "league": league.upper(),
                    "team1": t1['team']['shortDisplayName'],
                    "team2": t2['team']['shortDisplayName'],
                    "score1": t1.get('score', '0'),
                    "score2": t2.get('score', '0'),
                    "logo1": team1_logo_path,
                    "logo2": team2_logo_path
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

def safe_load_image(path):
    try:
        if isinstance(path, str) and os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        else:
            print(f"Invalid image path: {path}")
    except Exception as e:
        print(f"Failed to load image {path}: {e}")
    return None

def render_score_items(scores, font):
    surfaces = []
    for item in scores:
        score_text = f"{item['score1']} - {item['score2']}"
        score_surface = font.render(score_text, True, (255, 255, 255))

        logo1 = safe_load_image(item['logo1'][1]) if item['logo1'] else None
        logo2 = safe_load_image(item['logo2'][1]) if item['logo2'] else None

        # Use placeholders if logos are missing
        logo_size = 80
        placeholder = pygame.Surface((logo_size, logo_size), pygame.SRCALPHA)
        placeholder.fill((50, 50, 50))

        logo1 = pygame.transform.scale(logo1, (logo_size, logo_size)) if logo1 else placeholder
        logo2 = pygame.transform.scale(logo2, (logo_size, logo_size)) if logo2 else placeholder

        width = logo_size + 40 + score_surface.get_width() + 40 + logo_size
        surface = pygame.Surface((width, logo_size), pygame.SRCALPHA)

        surface.blit(logo1, (0, 0))
        surface.blit(score_surface, (logo_size + 40, (logo_size - score_surface.get_height()) // 2))
        surface.blit(logo2, (logo_size + 40 + score_surface.get_width() + 40, 0))

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

import rumps
import json
import csv
import os
import subprocess
from PIL import Image, ImageDraw

DATA_DIR = "data"
TROPHY_CSV = os.path.join(DATA_DIR, "trophies.csv")
CONFIG_JSON = os.path.join(DATA_DIR, "config.json")
EDITOR_APP_PATH = "maingui.py"  # Update this path!
TEMP_ICON_PATH = os.path.join(DATA_DIR, "temp_profile_icon.png")


def load_config():
    with open(CONFIG_JSON, 'r') as f:
        return json.load(f)


def load_trophies():
    with open(TROPHY_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return next(reader)


def calculate_points(trophies):
    TROPHY_VALUES = {"bronze": 15, "silver": 30, "gold": 90, "platinum": 300}
    return sum(int(trophies[t]) * TROPHY_VALUES[t] for t in TROPHY_VALUES)


def make_circle_icon(image_path, output_path, size=64):
    try:
        im = Image.open(image_path).convert("RGBA")
        # Crop to square
        min_side = min(im.size)
        left = (im.width - min_side) // 2
        top = (im.height - min_side) // 2
        im = im.crop((left, top, left + min_side, top + min_side))
        im = im.resize((size, size), Image.LANCZOS)
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        im.putalpha(mask)
        im.save(output_path)
        return output_path
    except Exception:
        return os.path.join(DATA_DIR, "menu_icon.png")


class PSNTrophyMenuApp(rumps.App):
    def __init__(self):
        self.config = load_config()
        self.trophies = load_trophies()
        self.points = calculate_points(self.trophies)
        default_icon = os.path.join(DATA_DIR, "menu_icon.png")
        super().__init__("🎮", icon=default_icon, menu=[
            "Loading...",
            None,
            rumps.MenuItem("Edit Profile", callback=self.launch_editor),
            rumps.MenuItem("Quit", callback=self.quit_app)
        ])
        self.update_subtitle_and_icon()
        self.timer = rumps.Timer(self.refresh_menu, 1)  # every 1 second
        self.timer.start()

    def refresh_menu(self, _):
        self.update_subtitle_and_icon()
        self.menu.clear()
        self.menu.add(self.subtitle)
        self.menu.add(None)
        self.menu.add(rumps.MenuItem(
            "Edit Profile", callback=self.launch_editor))
        self.menu.add(rumps.MenuItem("Quit", callback=self.quit_app))

    def update_subtitle_and_icon(self):
        config = load_config()
        trophies = load_trophies()
        points = calculate_points(trophies)

        LEVEL_THRESHOLDS = [
            (1, 99, 60),
            (100, 199, 90),
            (200, 299, 450),
            (300, 399, 900),
            (400, 499, 1350),
            (500, 599, 1800),
            (600, 699, 2250),
            (700, 799, 2700),
            (800, 899, 3150),
            (900, 999, 3600)
        ]

        def calculate_level(points):
            level = 1
            total = 0
            for start, end, inc in LEVEL_THRESHOLDS:
                for _ in range(start, end + 1):
                    if total + inc > points:
                        return level, points - total, inc
                    total += inc
                    level += 1
            return 999, points, 1

        level, current, required = calculate_level(points)
        percent = int((current / required) * 100) if required else 100
        trophy_total = sum(int(trophies[t]) for t in trophies)

        self.subtitle = f"{config['username']} | Lv. {level} | {percent}% | {trophy_total} trophies"

        profile_icon = config.get("profile_path", "")
        if not (profile_icon and os.path.exists(profile_icon)):
            profile_icon = os.path.join(DATA_DIR, "menu_icon.png")
        # Always make the icon circular
        self.profile_icon = make_circle_icon(profile_icon, TEMP_ICON_PATH)
        self.icon = self.profile_icon

    def launch_editor(self, _):
        subprocess.Popen(["python3", EDITOR_APP_PATH])

    def quit_app(self, _):
        rumps.quit_application()


if __name__ == '__main__':
    PSNTrophyMenuApp().run()

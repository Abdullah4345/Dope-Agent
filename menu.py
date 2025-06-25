import rumps
import json
import csv
import os
import subprocess

DATA_DIR = "data"
TROPHY_CSV = os.path.join(DATA_DIR, "trophies.csv")
CONFIG_JSON = os.path.join(DATA_DIR, "config.json")
EDITOR_APP_PATH = "maingui.py"  # Update this path!


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


class PSNTrophyMenuApp(rumps.App):
    def __init__(self):
        config = load_config()
        trophies = load_trophies()
        points = calculate_points(trophies)

        # Level and percentage calculation (copied from your main copy 3.py)
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

        subtitle = f"{config['username']} | Lv. {level} | {percent}% | {trophy_total} trophies"

        # Use profile picture if it exists, else fallback to default icon
        profile_icon = config.get("profile_path", "")
        if not (profile_icon and os.path.exists(profile_icon)):
            profile_icon = os.path.join(DATA_DIR, "menu_icon.png")
        super().__init__("🎮", icon=profile_icon, menu=[
            subtitle,
            None,
            "Edit Profile",
            "Quit"
        ])

    @rumps.clicked("Edit Profile")
    def launch_editor(self, _):
        subprocess.Popen(["python3", EDITOR_APP_PATH])

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()


if __name__ == '__main__':
    PSNTrophyMenuApp().run()

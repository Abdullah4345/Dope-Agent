import sys
import subprocess
import os
import json
import csv
import rumps
import AppKit
from PIL import Image, ImageDraw
import socket
import objc


# --- Draggable area class (move to top of file) ---
class DraggableTopView(AppKit.NSView):
    def initWithWindow_(self, window):
        self = objc.super(DraggableTopView, self).init()
        self.window = window
        self.drag_start = None
        return self

    def mouseDown_(self, event):
        self.drag_start = event.locationInWindow()

    def mouseDragged_(self, event):
        if self.drag_start is not None:
            curr_pos = event.locationInWindow()
            dx = curr_pos.x - self.drag_start.x
            dy = curr_pos.y - self.drag_start.y
            frame = self.window.frame()
            new_origin = AppKit.NSPoint(
                frame.origin.x + dx, frame.origin.y + dy)
            self.window.setFrameOrigin_(new_origin)


# --- Shared resource path and data logic ---
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


DATA_DIR = resource_path("data")
TROPHY_CSV = os.path.join(DATA_DIR, "trophies.csv")
CONFIG_JSON = os.path.join(DATA_DIR, "config.json")
TEMP_ICON_PATH = os.path.join(DATA_DIR, "temp_profile_icon.png")


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_JSON):
        default_config = {"username": "",
                          "profile_path": "", "banner_path": ""}
        with open(CONFIG_JSON, 'w') as f:
            json.dump(default_config, f)
    if not os.path.exists(TROPHY_CSV):
        default_trophies = {"bronze": 0, "silver": 0, "gold": 0, "platinum": 0}
        with open(TROPHY_CSV, 'w', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=default_trophies.keys())
            writer.writeheader()
            writer.writerow(default_trophies)


def load_config():
    with open(CONFIG_JSON, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_JSON, 'w') as f:
        json.dump(config, f)


def load_trophies():
    with open(TROPHY_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return next(reader)


def save_trophies(trophies):
    row = {k: str(v) for k, v in trophies.items()}
    with open(TROPHY_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
                                "bronze", "silver", "gold", "platinum"])
        writer.writeheader()
        writer.writerow(row)


def has_internet(host="8.8.8.8", port=53, timeout=2):
    """Check for internet connection by trying to connect to a DNS server."""
    import socket
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def run_dashboard():
    import json
    import csv
    import os
    import sys
    from Cocoa import NSWindow, NSApp, NSImageView, NSImage, NSTextField, NSButton, NSVisualEffectView, NSVisualEffectMaterialHUDWindow, NSOpenPanel, NSBackingStoreBuffered, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskFullSizeContentView
    from Foundation import NSObject, NSMakeRect
    import AppKit
    import objc
    from WebKit import WKWebView, WKWebViewConfiguration
    from Cocoa import NSFloatingWindowLevel, NSBorderlessWindowMask
    import threading

    try:
        from ScriptingBridge import SBApplication
    except ImportError:
        # ScriptingBridge only available if pyobjc-framework-ScriptingBridge is installed
        SBApplication = None

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller/py2app bundle """
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            base_path = sys._MEIPASS
        elif getattr(sys, 'frozen', False):
            # py2app or other frozen
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal script
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    DATA_DIR = resource_path("data")
    TROPHY_CSV = resource_path("data/trophies.csv")
    CONFIG_JSON = resource_path("data/config.json")
    TROPHY_PNGS = {
        "bronze": resource_path("data/bronze.png"),
        "silver": resource_path("data/silver.png"),
        "gold": resource_path("data/gold.png"),
        "platinum": resource_path("data/platinum.png")
    }
    TODO_JSON = resource_path("data/todo.json")

    def ensure_data_files():
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_JSON):
            default_config = {"username": "",
                              "profile_path": "", "banner_path": ""}
            with open(CONFIG_JSON, 'w') as f:
                json.dump(default_config, f)
        if not os.path.exists(TROPHY_CSV):
            default_trophies = {"bronze": 0,
                                "silver": 0, "gold": 0, "platinum": 0}
            with open(TROPHY_CSV, 'w', newline='') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=default_trophies.keys())
                writer.writeheader()
                writer.writerow(default_trophies)

    def load_config():
        with open(CONFIG_JSON, 'r') as f:
            return json.load(f)

    def save_config(config):
        with open(CONFIG_JSON, 'w') as f:
            json.dump(config, f)

    def load_trophies():
        with open(TROPHY_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return next(reader)

    def save_trophies(trophies):
        row = {k: str(v) for k, v in trophies.items()}
        with open(TROPHY_CSV, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                                    "bronze", "silver", "gold", "platinum"])
            writer.writeheader()
            writer.writerow(row)

    def load_todos():
        if not os.path.exists(TODO_JSON):
            return []
        with open(TODO_JSON, "r") as f:
            return json.load(f)

    def save_todos(todos):
        with open(TODO_JSON, "w") as f:
            json.dump(todos, f)

    class ButtonHelper(NSObject):
        def initWithConfig_(self, config):
            self = objc.super(ButtonHelper, self).init()
            self.config = config
            return self

        def choosePic_(self, sender):
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowedFileTypes_(["png", "jpg", "jpeg"])
            if panel.runModal():
                url = panel.URLs()[0] if panel.URLs() else None
                if url:
                    self.config["profile_path"] = url.path()
                    save_config(self.config)

    class SaveHelper(NSObject):
        def init(self):
            self = objc.super(SaveHelper, self).init()
            self.config = None
            self.fields = None
            self.trophies = None
            self.window = None
            return self

        def setAll_(self, args):
            self.config, self.fields, self.trophies, self.window = args

        def saveChanges_(self, sender):
            self.config["username"] = str(
                self.fields["username"].stringValue())
            save_config(self.config)
            for t in ["platinum", "gold", "silver", "bronze"]:
                val = str(self.fields[t].stringValue())
                self.trophies[t] = val if val.isdigit() else "0"
            save_trophies(self.trophies)
            self.window.orderOut_(None)  # Hide window

    class WindowDelegate(NSObject):
        def windowShouldClose_(self, sender):
            AppKit.NSApp().stop_(None)  # Stop the event loop
            return True

    class ClickableImageView(NSImageView):
        def initWithConfig_(self, config):
            self = objc.super(ClickableImageView, self).init()
            self.config = config
            return self

        def mouseDown_(self, event):
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowedFileTypes_(["png", "jpg", "jpeg"])
            if panel.runModal():
                url = panel.URLs()[0] if panel.URLs() else None
                if url:
                    self.config["profile_path"] = url.path()
                    save_config(self.config)
                    # Update the image in the view
                    new_img = NSImage.alloc().initWithContentsOfFile_(url.path())
                    new_img = crop_to_square(new_img)
                    self.setImage_(new_img)

    class ClickableLabel(NSTextField):
        def init(self):
            self = objc.super(ClickableLabel, self).init()
            self.edit_field = None
            self.config = None
            return self

        def set_field_and_config(self, field, config):
            self.edit_field = field
            self.config = config

        def mouseDown_(self, event):
            self.setHidden_(True)
            self.edit_field.setHidden_(False)
            self.edit_field.becomeFirstResponder()

    class UsernameEditField(NSTextField):
        def init(self):
            self = objc.super(UsernameEditField, self).init()
            self.label = None
            self.config = None
            self.trophy_name = None  # Add this line
            return self

        def set_label_and_config(self, label, config):
            self.label = label
            self.config = config

        def textDidEndEditing_(self, notification):
            new_val = self.stringValue()
            if self.label:
                self.label.setStringValue_(new_val)
                self.label.setHidden_(False)
            self.setHidden_(True)
            # Save logic for username or trophy
            if self.trophy_name and self.config is not None:
                # It's a trophy field
                self.config[self.trophy_name] = new_val if new_val.isdigit(
                ) else "0"
                save_trophies(self.config)
            elif self.config is not None:
                # It's the username field
                self.config["username"] = new_val
                save_config(self.config)

    class TodoAddHelper(NSObject):
        def initWithTodoPanel_(self, todo_panel):
            self = objc.super(TodoAddHelper, self).init()
            self.todo_panel = todo_panel
            return self

        def addTodo_(self, sender):
            field = self.todo_panel["input"]
            item = field.stringValue().strip()
            if item:
                todos = load_todos()
                todos.append(item)
                save_todos(todos)
                field.setStringValue_("")
                self.todo_panel["refresh"]()

    class TodoRemoveHelper(NSObject):
        def initWithTodoPanel_andIndex_(self, todo_panel, idx):
            self = objc.super(TodoRemoveHelper, self).init()
            self.todo_panel = todo_panel
            self.idx = idx
            return self

        def removeTodo_(self, sender):
            todos = load_todos()
            if 0 <= self.idx < len(todos):
                del todos[self.idx]
                save_todos(todos)
                self.todo_panel["refresh"]()

    class TodoClearHelper(NSObject):
        def initWithTodoPanel_(self, todo_panel):
            self = objc.super(TodoClearHelper, self).init()
            self.todo_panel = todo_panel
            return self

        def clearTodos_(self, sender):
            save_todos([])
            self.todo_panel["refresh"]()

    class ShowTodoHelper(NSObject):
        def initWithWindow_andTodoVisual_(self, window, todo_visual):
            self = objc.super(ShowTodoHelper, self).init()
            self.window = window
            self.todo_visual = todo_visual
            return self

        def showTodo_(self, sender):
            self.todo_visual.setHidden_(False)
            frame = self.window.frame()
            new_frame = NSMakeRect(
                frame.origin.x,
                frame.origin.y,
                840,  # window_width_expanded
                470   # window_height
            )
            self.window.setFrame_display_animate_(new_frame, True)
            # Update content view and visual_effect frame after animation
            self.window.contentView().setFrame_(NSMakeRect(0, 0, 840, 470))
            self.window.contentView().superview().setFrame_(NSMakeRect(0, 0, 840, 470))
            self.window.contentView().subviews()[0].setFrame_(
                NSMakeRect(0, 0, 840, 470))  # visual_effect
            self.todo_visual.setFrame_(NSMakeRect(420, 0, 420, 470))
            sender.setHidden_(True)

    main_window = None
    air_widget_window = None  # <-- Add this line at the top-level

    def get_current_media_info():
        """Try to get currently playing media info from Music.app (macOS)."""
        if SBApplication is None:
            return None
        music = SBApplication.applicationWithBundleIdentifier_(
            "com.apple.Music")
        if not music or not music.isRunning():
            return None
        track = music.currentTrack()
        if not track:
            return None
        # Try to get artwork as NSImage
        artwork = None
        if track.artworks() and track.artworks().count() > 0:
            art = track.artworks().objectAtIndex_(0)
            if hasattr(art, 'data'):
                data = art.data()
                if data:
                    artwork = NSImage.alloc().initWithData_(data)
        return {
            "name": str(track.name() or ""),
            "artist": str(track.artist() or ""),
            "album": str(track.album() or ""),
            "artwork": artwork
        }

    def show_air_widget():
        print("show_air_widget called")  # Debug: function called
        global air_widget_window
        info = get_current_media_info()
        print(f"media info: {info}")  # Debug: print media info
        if not info:
            print("No media info found")  # Debug: no media
            return  # No media playing

        # Make the widget big and centered
        widget_width = 600
        widget_height = 220
        screen_frame = AppKit.NSScreen.mainScreen().frame()
        x = (screen_frame.size.width - widget_width) / 2
        y = (screen_frame.size.height - widget_height) / 2

        air_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, widget_width, widget_height),
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False
        )
        air_window.setLevel_(NSFloatingWindowLevel)
        air_window.setOpaque_(False)
        air_window.setBackgroundColor_(AppKit.NSColor.clearColor())
        air_window.setIgnoresMouseEvents_(False)
        air_window.setMovableByWindowBackground_(True)

        # Visual effect background
        effect = NSVisualEffectView.alloc().initWithFrame_(
            NSMakeRect(0, 0, widget_width, widget_height))
        effect.setMaterial_(NSVisualEffectMaterialHUDWindow)
        effect.setBlendingMode_(0)
        effect.setState_(1)
        air_window.setContentView_(effect)

        # Artwork (large)
        img_size = 180
        img_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(30, (widget_height - img_size) // 2, img_size, img_size))
        if info["artwork"]:
            img_view.setImage_(info["artwork"])
        else:
            img_view.setImage_(NSImage.imageNamed_("NSUser"))
        img_view.setImageScaling_(AppKit.NSImageScaleProportionallyUpOrDown)
        effect.addSubview_(img_view)

        # Song name (large font)
        name_field = NSTextField.labelWithString_(info["name"])
        name_field.setFont_(AppKit.NSFont.boldSystemFontOfSize_(28))
        name_field.setTextColor_(AppKit.NSColor.whiteColor())
        name_field.setBackgroundColor_(AppKit.NSColor.clearColor())
        name_field.setFrame_(NSMakeRect(230, 120, widget_width-250, 48))
        effect.addSubview_(name_field)

        # Artist/album (large font)
        artist_field = NSTextField.labelWithString_(
            f"{info['artist']} — {info['album']}")
        artist_field.setFont_(AppKit.NSFont.systemFontOfSize_(22))
        artist_field.setTextColor_(AppKit.NSColor.whiteColor())
        artist_field.setBackgroundColor_(AppKit.NSColor.clearColor())
        artist_field.setFrame_(NSMakeRect(230, 70, widget_width-250, 38))
        effect.addSubview_(artist_field)

        air_window.orderFrontRegardless_()
        air_widget_window = air_window

    def open_native_window():
        global main_window
        ensure_data_files()
        config = load_config()
        trophies = load_trophies()

        # Calculate points and percent for progress bar
        points = (
            int(trophies.get("bronze", 0)) * 15 +
            int(trophies.get("silver", 0)) * 30 +
            int(trophies.get("gold", 0)) * 90 +
            int(trophies.get("platinum", 0)) * 300
        )

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

        AppKit.NSApplication.sharedApplication()
        NSApp.activateIgnoringOtherApps_(True)
        window_width = 1240
        window_height = 470
        left_panel_width = 420
        collapsed_width = left_panel_width
        expanded_width = window_width

        screen_frame = AppKit.NSScreen.mainScreen().frame()
        # Center for collapsed and expanded
        collapsed_x = (screen_frame.size.width - collapsed_width) / 2
        expanded_x = (screen_frame.size.width - expanded_width) / 2
        y = (screen_frame.size.height - window_height) / 2

        # Create the window here
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(collapsed_x, y, collapsed_width, window_height),
            AppKit.NSWindowStyleMaskFullSizeContentView | AppKit.NSWindowStyleMaskResizable | AppKit.NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )

        # Start window in collapsed (profile only) mode, centered
        window.setTitleVisibility_(AppKit.NSWindowTitleHidden)
        window.setTitlebarAppearsTransparent_(True)
        window.setOpaque_(False)
        window.setBackgroundColor_(AppKit.NSColor.clearColor())
        window.setHasShadow_(True)

        window_delegate = WindowDelegate.alloc().init()
        window.setDelegate_(window_delegate)
        # --- Add visual effect view as content view ---
        visual_effect = NSVisualEffectView.alloc().initWithFrame_(
            NSMakeRect(0, 0, collapsed_width, window_height)
        )
        window.setContentView_(visual_effect)

        # --- Rounded corners ---
        window.contentView().setWantsLayer_(True)
        window.contentView().layer().setCornerRadius_(26)
        window.contentView().layer().setMasksToBounds_(True)
        visual_effect.setWantsLayer_(True)
        visual_effect.layer().setCornerRadius_(26)
        visual_effect.layer().setMasksToBounds_(True)

        config = load_config()
        username = config.get("username", "").strip()
        if username:
            window.setTitle_(f"{username}'s Profile")
        else:
            window.setTitle_("Profile")

        window.setOpaque_(False)
        window.setBackgroundColor_(AppKit.NSColor.clearColor())

        # Now you can safely set layer properties
        visual_effect.setWantsLayer_(True)
        visual_effect.layer().setCornerRadius_(26)
        visual_effect.layer().setMasksToBounds_(True)
        visual_effect.layer().setBackgroundColor_(
            AppKit.NSColor.clearColor().CGColor()
        )
        visual_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        visual_effect.setBlendingMode_(
            AppKit.NSVisualEffectBlendingModeBehindWindow)
        visual_effect.setState_(AppKit.NSVisualEffectStateActive)

        # --- Add left panel view (move this up here!) ---
        left_panel = AppKit.NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, left_panel_width, window_height)
        )
        left_panel.setAutoresizingMask_(AppKit.NSViewHeightSizable)
        visual_effect.addSubview_(left_panel)

        # --- Make right half background a bit dark ---
        right_overlay = AppKit.NSView.alloc().initWithFrame_(
            NSMakeRect(left_panel_width, 0, window_width -
                       left_panel_width, window_height)
        )
        right_overlay.setWantsLayer_(True)
        right_overlay.layer().setBackgroundColor_(
            AppKit.NSColor.blackColor().colorWithAlphaComponent_(0.35).CGColor()
        )
        visual_effect.addSubview_positioned_relativeTo_(
            right_overlay, AppKit.NSWindowBelow, None
        )

        fields = {}
        profile_pic_path = config.get("profile_path", "")
        if os.path.exists(profile_pic_path):
            profile_img = NSImage.alloc().initWithContentsOfFile_(profile_pic_path)
            profile_img = crop_to_square(profile_img)
        else:
            profile_img = NSImage.imageNamed_("NSUser")
            profile_img = crop_to_square(profile_img)
        img_width = 100
        # Centered in left panel
        profile_img_view = ClickableImageView.alloc().initWithConfig_(config).initWithFrame_(
            NSMakeRect((left_panel_width - img_width) //
                       2, 320, img_width, img_width)
        )
        profile_img_view.setImage_(profile_img)
        profile_img_view.setImageScaling_(
            AppKit.NSImageScaleProportionallyUpOrDown)
        profile_img_view.setWantsLayer_(True)
        layer = profile_img_view.layer()
        layer.setCornerRadius_(img_width / 2)
        layer.setMasksToBounds_(True)
        visual_effect.addSubview_(profile_img_view)

        # Username edit field (hidden by default)
        username_field = UsernameEditField.alloc().init()
        username_field.setFrame_(NSMakeRect(
            (left_panel_width - 200) // 2, 290, 200, 24))
        username = config.get("username", "")
        username_field.setStringValue_(username)
        username_field.setHidden_(True)
        visual_effect.addSubview_(username_field)
        fields["username"] = username_field

        # Username label (shown by default)
        username_label = ClickableLabel.labelWithString_(username)
        username_label.setFrame_(NSMakeRect(
            (left_panel_width - 200) // 2, 290, 200, 24))
        username_label.setAlignment_(AppKit.NSCenterTextAlignment)
        username_label.setFont_(AppKit.NSFont.systemFontOfSize_(16))
        username_label.set_field_and_config(username_field, config)
        visual_effect.addSubview_(username_label)
        username_field.set_label_and_config(username_label, config)

        # Progress bar just above trophies row
        progress_bar = AppKit.NSProgressIndicator.alloc().initWithFrame_(
            NSMakeRect(30, 200, left_panel_width - 100, 16)
        )
        progress_bar.setIndeterminate_(False)
        progress_bar.setMinValue_(0)
        progress_bar.setMaxValue_(100)
        progress_bar.setDoubleValue_(percent)
        progress_bar.setStyle_(AppKit.NSProgressIndicatorBarStyle)
        visual_effect.addSubview_(progress_bar)

        percent_label = NSTextField.labelWithString_(f"{percent}%")
        percent_label.setTextColor_(AppKit.NSColor.whiteColor())
        percent_label.setBackgroundColor_(AppKit.NSColor.clearColor())
        percent_label.setAlignment_(AppKit.NSCenterTextAlignment)
        percent_label.setFrame_(NSMakeRect(left_panel_width - 60, 193, 50, 24))
        percent_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        visual_effect.addSubview_(percent_label)

        # Trophies row
        y_img = 140
        y_field = 110
        trophy_types = ["platinum", "gold", "silver", "bronze"]
        num_trophies = len(trophy_types)
        img_size = 48
        margin = 30
        available_width = left_panel_width - 2 * margin
        spacing = (available_width - num_trophies *
                   img_size) // (num_trophies - 1)
        x_offset = margin

        for name in trophy_types:
            img_path = TROPHY_PNGS.get(name)
            if os.path.exists(img_path):
                nsimg = NSImage.alloc().initWithContentsOfFile_(img_path)
            else:
                nsimg = NSImage.imageNamed_("NSCaution")
            img_view = NSImageView.alloc().initWithFrame_(
                NSMakeRect(x_offset, y_img, img_size, img_size))
            img_view.setImage_(nsimg)
            visual_effect.addSubview_(img_view)

            trophy_field = UsernameEditField.alloc().init()
            trophy_field.setFrame_(NSMakeRect(x_offset, y_field, img_size, 24))
            trophy_field.setStringValue_(trophies.get(name, "0"))
            trophy_field.setHidden_(True)
            visual_effect.addSubview_(trophy_field)
            fields[name] = trophy_field

            trophy_label = ClickableLabel.labelWithString_(
                trophies.get(name, "0"))
            trophy_label.setFrame_(NSMakeRect(x_offset, y_field, img_size, 24))
            trophy_label.setAlignment_(AppKit.NSCenterTextAlignment)
            trophy_label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
            trophy_label.set_field_and_config(trophy_field, trophies)
            visual_effect.addSubview_(trophy_label)
            trophy_field.set_label_and_config(trophy_label, trophies)
            trophy_field.trophy_name = name

            label = NSTextField.labelWithString_(name.title())
            label.setAlignment_(AppKit.NSCenterTextAlignment)
            label.setFrame_(NSMakeRect(
                x_offset - 10, y_field - 20, img_size + 20, 20))
            visual_effect.addSubview_(label)

            x_offset += img_size + spacing

        # User level icon and label
        level_icon_path = get_level_icon(level)
        if os.path.exists(level_icon_path):
            level_icon = NSImage.alloc().initWithContentsOfFile_(level_icon_path)
        else:
            level_icon = NSImage.imageNamed_("NSUser")

        icon_size = 40
        icon_x = 120
        icon_y = 240
        level_icon_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(icon_x, icon_y, icon_size, icon_size)
        )
        level_icon_view.setImage_(level_icon)
        level_icon_view.setImageScaling_(
            AppKit.NSImageScaleProportionallyUpOrDown)
        visual_effect.addSubview_(level_icon_view)

        level_label = NSTextField.labelWithString_(f"Level {level}")
        level_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(18))
        level_label.setTextColor_(AppKit.NSColor.whiteColor())
        level_label.setBackgroundColor_(AppKit.NSColor.clearColor())
        level_label.setAlignment_(AppKit.NSLeftTextAlignment)
        level_label.setFrame_(NSMakeRect(
            icon_x + icon_size + 10, icon_y + 8, 120, 24))
        visual_effect.addSubview_(level_label)

        # Banner view for profile (background)
        banner_height = 110  # Half the profile image height (img_width // 2)
        banner_width = 420
        banner_y = 370  # Start at the very top

        banner_path = config.get("banner_path", "")
        banner_img = None
        if banner_path and os.path.exists(banner_path):
            banner_img = NSImage.alloc().initWithContentsOfFile_(banner_path)
            banner_img = crop_to_banner(
                banner_img, banner_width, banner_height)
        if not banner_img:
            banner_img = NSImage.imageNamed_("NSColorPanel")
            banner_img = crop_to_banner(
                banner_img, banner_width, banner_height)

        banner_view = ClickableBannerView.alloc().initWithConfig_(config).initWithFrame_(
            NSMakeRect(0, banner_y, banner_width, banner_height)
        )
        banner_view.setImage_(banner_img)
        banner_view.setImageScaling_(AppKit.NSImageScaleAxesIndependently)
        visual_effect.addSubview_positioned_relativeTo_(
            banner_view, AppKit.NSWindowBelow, None
        )

        # Add a transparent drag handle ("__") on the banner near the top
        handle_width = 60
        handle_height = 18
        handle_x = (banner_width - handle_width) // 2
        handle_y = banner_y + banner_height - \
            handle_height - 20  # 8pt from top of banner

        class BannerDragHandle(DraggableTopView):
            def drawRect_(self, rect):
                handle_width = self.frame().size.width
                handle_height = self.frame().size.height
                # Draw a single connected rounded line ("__" with rounded ends)
                path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                    AppKit.NSMakeRect(8, handle_height // 2 -
                                      4, handle_width - 16, 8),
                    4, 4
                )
                AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.12).set()
                path.fill()

        banner_drag_handle = BannerDragHandle.alloc().initWithWindow_(window).initWithFrame_(
            AppKit.NSMakeRect(handle_x, handle_y, handle_width, handle_height)
        )
        banner_drag_handle.setWantsLayer_(True)
        banner_drag_handle.layer().setBackgroundColor_(
            AppKit.NSColor.clearColor().CGColor())
        visual_effect.addSubview_(banner_drag_handle)

        # --- Modern browser bar (right side, above browser) ---
        bar_height = 60
        bar_y = window_height - bar_height
        bar_x = left_panel_width
        bar_width = window_width - left_panel_width  # now 820

        browser_bar = NSVisualEffectView.alloc().initWithFrame_(
            NSMakeRect(bar_x, bar_y, bar_width, bar_height)
        )
        browser_bar.setMaterial_(NSVisualEffectMaterialHUDWindow)
        browser_bar.setBlendingMode_(0)
        browser_bar.setState_(1)
        browser_bar.setHidden_(True)
        visual_effect.addSubview_(browser_bar)

        # --- Add browser to the right side, initially hidden ---
        webview_config = WKWebViewConfiguration.alloc().init()
        browser = WKWebView.alloc().initWithFrame_configuration_(
            NSMakeRect(
                left_panel_width,
                0,
                window_width - left_panel_width,  # now 820
                window_height - bar_height
            ),
            webview_config
        )
        browser.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        # Username from config
        username = config.get("username", "").strip()
        if username:
            profile_url = f"https://psnprofiles.com/{username}"
        else:
            profile_url = "https://psnprofiles.com"
        url = AppKit.NSURL.URLWithString_(profile_url)
        request = AppKit.NSURLRequest.requestWithURL_(url)
        browser.loadRequest_(request)
        browser.setHidden_(True)
        visual_effect.addSubview_(browser)

        # Back button
        back_btn = NSButton.alloc().initWithFrame_(NSMakeRect(8, 4, 28, 28))
        back_btn.setTitle_("⟨")
        back_btn.setFont_(AppKit.NSFont.systemFontOfSize_(18))
        browser_bar.addSubview_(back_btn)

        # Forward button
        fwd_btn = NSButton.alloc().initWithFrame_(NSMakeRect(40, 4, 28, 28))
        fwd_btn.setTitle_("⟩")
        fwd_btn.setFont_(AppKit.NSFont.systemFontOfSize_(18))
        browser_bar.addSubview_(fwd_btn)

        # Refresh button
        refresh_btn = NSButton.alloc().initWithFrame_(NSMakeRect(72, 4, 28, 28))
        refresh_btn.setTitle_("⟳")
        refresh_btn.setFont_(AppKit.NSFont.systemFontOfSize_(16))
        browser_bar.addSubview_(refresh_btn)

        # Address field (read-only)
        addr_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(108, 6, bar_width - 116, 24)  # bar_width is now 820
        )
        addr_field.setEditable_(False)
        addr_field.setBezeled_(True)
        addr_field.setDrawsBackground_(True)
        addr_field.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        # <--- Set the address field to the actual URL
        addr_field.setStringValue_(profile_url)
        browser_bar.addSubview_(addr_field)

        # --- Button actions ---
        class BrowserBarHelper(NSObject):
            def initWithBrowser_andAddrField_(self, browser, addr_field):
                self = objc.super(BrowserBarHelper, self).init()
                self.browser = browser
                self.addr_field = addr_field
                return self

            def goBack_(self, sender):
                if self.browser.canGoBack():
                    self.browser.goBack()

            def goForward_(self, sender):
                if self.browser.canGoForward():
                    self.browser.goForward()

            def refresh_(self, sender):
                self.browser.reload()

        browser_bar_helper = BrowserBarHelper.alloc(
        ).initWithBrowser_andAddrField_(browser, addr_field)
        back_btn.setTarget_(browser_bar_helper)
        back_btn.setAction_("goBack:")
        fwd_btn.setTarget_(browser_bar_helper)
        fwd_btn.setAction_("goForward:")
        refresh_btn.setTarget_(browser_bar_helper)
        refresh_btn.setAction_("refresh:")

        # --- Update address field on navigation ---
        class BrowserDelegate(NSObject):
            def initWithBrowser_andAddrField_(self, browser, addr_field):
                self = objc.super(BrowserDelegate, self).init()
                self._browser = browser
                self.addr_field = addr_field
                return self

            def webView_didFinishNavigation_(self, webview, nav):
                js = "document.body.style.zoom='0.7';"
                self._browser.evaluateJavaScript_completionHandler_(js, None)
                # Update address field
                url = str(webview.URL().absoluteString())
                self.addr_field.setStringValue_(url)

        browser_delegate = BrowserDelegate.alloc(
        ).initWithBrowser_andAddrField_(browser, addr_field)
        browser.setNavigationDelegate_(browser_delegate)

        # --- Add "Open Guide" button centered in the right half ---
        btn_width = 160
        btn_height = 40
        btn_x = left_panel_width + \
            ((window_width - left_panel_width) - btn_width) // 2
        btn_y = (window_height - btn_height) // 2

        # --- Add browser.png or internet.png above the button ---
        img_width = 64
        img_height = 64
        img_x = left_panel_width + \
            ((window_width - left_panel_width) - img_width) // 2
        img_y = btn_y + btn_height + 20  # 20px above the button

        if has_internet():
            img_path = resource_path("data/browser.png")
            show_guide_btn = True
            guide_img_path = resource_path("data/guide.png")
        else:
            img_path = resource_path("data/internet.png")
            show_guide_btn = False
            guide_img_path = resource_path("data/guide-no-internet.png")

        browser_img = NSImage.alloc().initWithContentsOfFile_(img_path)
        browser_img_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(img_x, img_y, img_width, img_height)
        )
        browser_img_view.setImage_(browser_img)
        browser_img_view.setImageScaling_(
            AppKit.NSImageScaleProportionallyUpOrDown)
        visual_effect.addSubview_(browser_img_view)

        # Use guide_img_path here
        guide_img = NSImage.alloc().initWithContentsOfFile_(guide_img_path)

        open_guide_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect(btn_x, btn_y, btn_width, btn_height)
        )
        open_guide_btn.setTitle_("Open Guide")
        open_guide_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        open_guide_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        visual_effect.addSubview_(open_guide_btn)

        # Add toggle button to left panel (as a circular image button)
        guide_btn_size = 30  # Make the button a bit larger
        guide_btn_x = (left_panel_width - guide_btn_size) // 2
        guide_btn_y = 30

        # Use the same guide_img_path as above, so it matches internet status
        # guide_img_path is already set above based on has_internet()
        guide_img = NSImage.alloc().initWithContentsOfFile_(guide_img_path)

        # Scale the image down to fit nicely inside the button (e.g., 22x22)
        icon_size = 22
        small_guide_img = NSImage.alloc().initWithSize_((icon_size, icon_size))
        small_guide_img.lockFocus()
        guide_img.drawInRect_fromRect_operation_fraction_(
            AppKit.NSMakeRect(0, 0, icon_size, icon_size),
            AppKit.NSMakeRect(0, 0, guide_img.size().width,
                              guide_img.size().height),
            AppKit.NSCompositingOperationSourceOver,
            1.0
        )
        small_guide_img.unlockFocus()

        toggle_guide_btn = NSButton.alloc().initWithFrame_(
            NSMakeRect(guide_btn_x, guide_btn_y,
                       guide_btn_size, guide_btn_size)
        )
        toggle_guide_btn.setImage_(small_guide_img)
        toggle_guide_btn.setBezelStyle_(AppKit.NSBezelStyleCircular)
        toggle_guide_btn.setTitle_("")  # No text
        toggle_guide_btn.setImageScaling_(AppKit.NSImageScaleNone)
        toggle_guide_btn.setBordered_(False)
        toggle_guide_btn.setWantsLayer_(True)
        toggle_guide_btn.layer().setCornerRadius_(guide_btn_size / 2)
        toggle_guide_btn.layer().setMasksToBounds_(True)
        left_panel.addSubview_(toggle_guide_btn)

        if not show_guide_btn:
            open_guide_btn.setHidden_(True)
            # Also hide browser and browser bar forever if no internet
            browser.setHidden_(True)
            browser_bar.setHidden_(True)
            # Optionally, you can also disable the toggle_guide_btn if you want:
            toggle_guide_btn.setEnabled_(False)
        else:
            # --- Button action to show browser and bar, and hide itself and image ---
            class OpenGuideHelper(NSObject):
                def initWithBrowser_andButton_andImage_andBar_(self, browser, button, img_view, bar):
                    self = objc.super(OpenGuideHelper, self).init()
                    self.browser = browser
                    self.button = button
                    self.img_view = img_view
                    self.bar = bar
                    return self

                def openGuide_(self, sender):
                    self.browser.setHidden_(False)
                    self.button.setHidden_(True)
                    self.img_view.setHidden_(True)
                    self.bar.setHidden_(False)

            open_guide_helper = OpenGuideHelper.alloc(
            ).initWithBrowser_andButton_andImage_andBar_(browser, open_guide_btn, browser_img_view, browser_bar)
            open_guide_btn.setTarget_(open_guide_helper)
            open_guide_btn.setAction_("openGuide:")

            # Enable the toggle_guide_btn if you want:
            toggle_guide_btn.setEnabled_(True)

        # Set initial window size to collapsed (left panel only)
        window.setFrame_display_animate_(
            NSMakeRect(collapsed_x, y, collapsed_width,
                       window_height), True, False
        )

        # Make window resizable with reasonable min/max
        window.setMinSize_(AppKit.NSMakeSize(collapsed_width, window_height))
        window.setMaxSize_(AppKit.NSMakeSize(expanded_width, window_height))

        # Make overlays and browser autoresize
        visual_effect.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        right_overlay.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        browser.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        browser_bar.setAutoresizingMask_(AppKit.NSViewWidthSizable)

        # Hide browser and bar initially
        browser.setHidden_(True)
        browser_bar.setHidden_(True)

        class GuideToggleHelper(NSObject):
            def initWithWindow_andBrowser_andBar_andBtn_andImg_andOpenBtn_(self, window, browser, browser_bar, toggle_btn, img_view, open_guide_btn):
                self = objc.super(GuideToggleHelper, self).init()
                self.window = window
                self.browser = browser
                self.browser_bar = browser_bar
                self.toggle_btn = toggle_btn
                self.img_view = img_view
                self.open_guide_btn = open_guide_btn
                self.expanded = False
                return self

            @objc.typedSelector(b'v@:@')
            def toggleGuide_(self, sender):
                print("Guide button pressed")  # Debug
                screen_frame = AppKit.NSScreen.mainScreen().frame()
                full_width = 1240
                collapsed_width = 420
                expanded_x = (screen_frame.size.width - full_width) / 2
                collapsed_x = (screen_frame.size.width - collapsed_width) / 2
                y = self.window.frame().origin.y  # Keep current y

                def update_browser_frames():
                    frame = self.window.frame()
                    self.browser.setFrame_(AppKit.NSMakeRect(
                        420, 0, frame.size.width - 420, frame.size.height - 60))
                    self.browser_bar.setFrame_(AppKit.NSMakeRect(
                        420, frame.size.height - 60, frame.size.width - 420, 60))

                AppKit.NSAnimationContext.beginGrouping()
                context = AppKit.NSAnimationContext.currentContext()
                context.setDuration_(0.35)  # Animation duration in seconds

                if not self.expanded:
                    # Expand window to show right half, centered
                    context.setCompletionHandler_(update_browser_frames)
                    self.window.animator().setFrame_display_(
                        AppKit.NSMakeRect(expanded_x, y, full_width, 470), True
                    )
                    self.browser.setHidden_(False)
                    self.browser_bar.setHidden_(False)
                    self.img_view.setHidden_(True)
                    self.open_guide_btn.setHidden_(True)
                    self.expanded = True
                else:
                    # Collapse window to left half only, centered
                    context.setCompletionHandler_(update_browser_frames)
                    self.window.animator().setFrame_display_(
                        AppKit.NSMakeRect(
                            collapsed_x, y, collapsed_width, 470), True
                    )
                    self.browser.setHidden_(True)
                    self.browser_bar.setHidden_(True)
                    self.img_view.setHidden_(False)
                    self.open_guide_btn.setHidden_(False)
                    self.expanded = False

                AppKit.NSAnimationContext.endGrouping()

        guide_toggle_helper = GuideToggleHelper.alloc().initWithWindow_andBrowser_andBar_andBtn_andImg_andOpenBtn_(
            window, browser, browser_bar, toggle_guide_btn, browser_img_view, open_guide_btn)
        toggle_guide_btn.setTarget_(guide_toggle_helper)
        toggle_guide_btn.setAction_("toggleGuide:")
        toggle_guide_btn.setEnabled_(True)

        # --- Transparent "X" close button at top left ---
        close_btn_size = 26
        close_btn_x = 16  # 16pt from left edge
        close_btn_y = window_height - close_btn_size - 16  # 16pt from top edge

        close_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(close_btn_x, close_btn_y,
                              close_btn_size, close_btn_size)
        )
        close_btn.setTitle_("✕")
        close_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(18))
        close_btn.setBezelStyle_(AppKit.NSBezelStyleCircular)
        close_btn.setBordered_(False)
        close_btn.setWantsLayer_(True)
        close_btn.layer().setCornerRadius_(close_btn_size / 2)
        close_btn.layer().setBackgroundColor_(
            AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.2).CGColor())
        close_btn.layer().setMasksToBounds_(True)

        class CloseHelper(objc.lookUpClass("NSObject")):
            def initWithWindow_(self, window):
                self = objc.super(CloseHelper, self).init()
                self.window = window
                return self

            @objc.typedSelector(b'v@:@')
            def close_(self, sender):
                AppKit.NSApp.terminate_(None)  # Fully quit the app

        close_helper = CloseHelper.alloc().initWithWindow_(window)
        close_btn.setTarget_(close_helper)
        close_btn.setAction_("close:")

        visual_effect.addSubview_(close_btn)

        # --- Draggable area at top middle ---
        drag_area_width = 180
        drag_area_height = 36
        drag_area_x = (window_width - drag_area_width) // 2
        drag_area_y = window_height - drag_area_height - 8  # 8pt from top edge

        draggable_top = DraggableTopView.alloc().initWithWindow_(window).initWithFrame_(
            AppKit.NSMakeRect(drag_area_x, drag_area_y,
                              drag_area_width, drag_area_height)
        )
        draggable_top.setAutoresizingMask_(AppKit.NSViewMinYMargin)
        draggable_top.setWantsLayer_(True)
        draggable_top.layer().setBackgroundColor_(
            AppKit.NSColor.clearColor().CGColor())
        visual_effect.addSubview_(draggable_top)

        # Show the window at the end
        window.makeKeyAndOrderFront_(None)

        AppKit.NSApp.run()

    def get_level_icon(level):
        if level >= 900:
            return resource_path("data/999.png")
        elif level >= 800:
            return resource_path("data/800-899.png")
        elif level >= 700:
            return resource_path("data/700-799.png")
        elif level >= 600:
            return resource_path("data/600-699.png")
        elif level >= 500:
            return resource_path("data/500-599.png")
        elif level >= 400:
            return resource_path("data/400-499.png")
        elif level >= 300:
            return resource_path("data/300-399.png")
        elif level >= 200:
            return resource_path("data/200-299.png")
        elif level >= 100:
            return resource_path("data/100-199.png")
        else:
            return resource_path("data/1-99.png")

    def crop_to_square(nsimage):
        """Crop the NSImage to a centered square and return a new NSImage."""
        size = min(nsimage.size().width, nsimage.size().height)
        x = (nsimage.size().width - size) / 2
        y = (nsimage.size().height - size) / 2
        rect = AppKit.NSMakeRect(x, y, size, size)
        cropped = AppKit.NSImage.alloc().initWithSize_((size, size))
        cropped.lockFocus()
        nsimage.drawInRect_fromRect_operation_fraction_(
            AppKit.NSMakeRect(0, 0, size, size),
            rect,
            AppKit.NSCompositingOperationCopy,
            1.0
        )
        cropped.unlockFocus()
        return cropped

    class ClickableBannerView(NSImageView):
        def initWithConfig_(self, config):
            self = objc.super(ClickableBannerView, self).init()
            self.config = config
            return self

        def mouseDown_(self, event):
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowedFileTypes_(["png", "jpg", "jpeg"])
            if panel.runModal():
                url = panel.URLs()[0] if panel.URLs() else None
                if url:
                    self.config["banner_path"] = url.path()
                    save_config(self.config)
                    # Load and crop the new image
                    new_img = NSImage.alloc().initWithContentsOfFile_(url.path())
                    frame = self.frame()
                    new_img = crop_to_banner(new_img, int(
                        frame.size.width), int(frame.size.height))
                    self.setImage_(new_img)

    def crop_to_banner(nsimage, target_width, target_height):
        """Crop and scale NSImage to fill a banner rectangle."""
        img_w = nsimage.size().width
        img_h = nsimage.size().height
        target_ratio = target_width / target_height
        img_ratio = img_w / img_h

        # Determine crop area
        if img_ratio > target_ratio:
            # Image is wider than target: crop sides
            new_w = img_h * target_ratio
            x = (img_w - new_w) / 2
            rect = AppKit.NSMakeRect(x, 0, new_w, img_h)
        else:
            # Image is taller than target: crop top/bottom
            new_h = img_w / target_ratio
            y = (img_h - new_h) / 2
            rect = AppKit.NSMakeRect(0, y, img_w, new_h)

        cropped = AppKit.NSImage.alloc().initWithSize_((target_width, target_height))
        cropped.lockFocus()
        nsimage.drawInRect_fromRect_operation_fraction_(
            AppKit.NSMakeRect(0, 0, target_width, target_height),
            rect,
            AppKit.NSCompositingOperationCopy,
            1.0
        )
        cropped.unlockFocus()
        return cropped

    class ToggleTodoHelper(NSObject):
        def initWithWindow_andTodoVisual_andButton_(self, window, todo_visual, toggle_btn):
            self = objc.super(ToggleTodoHelper, self).init()
            self.window = window
            self.todo_visual = todo_visual
            self.toggle_btn = toggle_btn
            self.expanded = True  # Start expanded
            return self

        def toggleTodo_(self, sender):
            frame = self.window.frame()
            if self.expanded:
                # Shrink window and hide to-do panel
                new_frame = NSMakeRect(
                    frame.origin.x,
                    frame.origin.y,
                    420,  # window_width_collapsed
                    470
                )
                self.window.setFrame_display_animate_(new_frame, True)
                self.todo_visual.setHidden_(True)
                self.toggle_btn.setTitle_("Show To-Do")
                self.expanded = False
            else:
                # Expand window and show to-do panel
                new_frame = NSMakeRect(
                    frame.origin.x,
                    frame.origin.y,
                    840,  # window_width_expanded
                    470
                )
                self.window.setFrame_display_animate_(new_frame, True)
                self.todo_visual.setHidden_(False)
                self.toggle_btn.setTitle_("Hide To-Do")
                self.expanded = True

    class AirWidgetLauncher(NSObject):
        def showAirWidget_(self, obj):
            show_air_widget()

    open_native_window()


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
            rumps.MenuItem("Profile", callback=self.launch_editor),
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
            "Profile", callback=self.launch_editor))
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
        subprocess.Popen([sys.executable, sys.argv[0], "--dashboard"])

    def quit_app(self, _):
        rumps.quit_application()


if __name__ == '__main__':
    if '--dashboard' in sys.argv:
        run_dashboard()
    else:
        AppKit.NSApplication.sharedApplication().setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory)
        PSNTrophyMenuApp().run()

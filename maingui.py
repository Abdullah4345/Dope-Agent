import json
import csv
import os
import sys
from Cocoa import NSWindow, NSApp, NSImageView, NSImage, NSTextField, NSButton, NSVisualEffectView, NSVisualEffectMaterialHUDWindow, NSOpenPanel, NSBackingStoreBuffered, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskFullSizeContentView
from Foundation import NSObject, NSMakeRect
import AppKit
import objc


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


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_JSON):
        default_config = {"username": "", "profile_path": ""}
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
        self.config["username"] = str(self.fields["username"].stringValue())
        save_config(self.config)
        for t in ["platinum", "gold", "silver", "bronze"]:
            val = str(self.fields[t].stringValue())
            self.trophies[t] = val if val.isdigit() else "0"
        save_trophies(self.trophies)
        self.window.orderOut_(None)  # Hide window


class WindowDelegate(NSObject):
    def initWithSaveHelper_(self, save_helper):
        self = objc.super(WindowDelegate, self).init()
        self.save_helper = save_helper
        return self

    def windowShouldClose_(self, sender):
        self.save_helper.saveChanges_(sender)
        sender.orderOut_(None)
        return False


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
            self.config[self.trophy_name] = new_val if new_val.isdigit() else "0"
            save_trophies(self.config)
        elif self.config is not None:
            # It's the username field
            self.config["username"] = new_val
            save_config(self.config)


def open_native_window():
    ensure_data_files()
    config = load_config()
    trophies = load_trophies()

    # Ensure NSApp is initialized
    AppKit.NSApplication.sharedApplication()

    NSApp.activateIgnoringOtherApps_(True)
    screen_frame = AppKit.NSScreen.mainScreen().frame()
    window_width = 420
    window_height = 470
    x = (screen_frame.size.width - window_width) / 2
    y = (screen_frame.size.height - window_height) / 2

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(x, y, window_width, window_height),
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskFullSizeContentView,
        NSBackingStoreBuffered,
        False
    )
    window.setTitle_("Edit PSN Profile")
    window.setOpaque_(False)
    visual_effect = NSVisualEffectView.alloc(
    ).initWithFrame_(window.contentView().frame())
    visual_effect.setMaterial_(NSVisualEffectMaterialHUDWindow)
    visual_effect.setBlendingMode_(0)
    visual_effect.setState_(1)
    window.setContentView_(visual_effect)

    fields = {}
    profile_pic_path = config.get("profile_path", "")
    if os.path.exists(profile_pic_path):
        profile_img = NSImage.alloc().initWithContentsOfFile_(profile_pic_path)
    else:
        profile_img = NSImage.imageNamed_("NSUser")
    # Centered profile image
    img_width = 100
    profile_img_view = ClickableImageView.alloc().initWithConfig_(config).initWithFrame_(
        NSMakeRect((window_width - img_width) // 2, 320, img_width, img_width)
    )
    profile_img_view.setImage_(profile_img)
    profile_img_view.setImageScaling_(
        AppKit.NSImageScaleProportionallyUpOrDown)
    visual_effect.addSubview_(profile_img_view)

    # Username edit field (hidden by default)
    username_field = UsernameEditField.alloc().init()
    username_field.setFrame_(NSMakeRect(
        (window_width - 200) // 2, 290, 200, 24))
    username = config.get("username", "")
    username_field.setStringValue_(username)
    username_field.setHidden_(True)
    visual_effect.addSubview_(username_field)
    fields["username"] = username_field

    # Username label (shown by default)
    username_label = ClickableLabel.labelWithString_(username)
    username_label.setFrame_(NSMakeRect(
        (window_width - 200) // 2, 290, 200, 24))
    username_label.setAlignment_(AppKit.NSCenterTextAlignment)
    username_label.setFont_(AppKit.NSFont.systemFontOfSize_(16))
    username_label.set_field_and_config(username_field, config)
    visual_effect.addSubview_(username_label)

    # Link the label to the field (so the field can update the label)
    username_field.set_label_and_config(username_label, config)

    # Calculate level and percent for progress bar
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

    points = sum(int(trophies[t]) * v for t, v in zip(["bronze",
                 "silver", "gold", "platinum"], [15, 30, 90, 300]))
    level, current, required = calculate_level(points)
    percent = int((current / required) * 100) if required else 100

    # Add progress bar just above trophies row
    progress_bar = AppKit.NSProgressIndicator.alloc().initWithFrame_(
        NSMakeRect(30, 200, window_width - 100, 16)  # leave space for % label
    )
    progress_bar.setIndeterminate_(False)
    progress_bar.setMinValue_(0)
    progress_bar.setMaxValue_(100)
    progress_bar.setDoubleValue_(percent)
    progress_bar.setStyle_(AppKit.NSProgressIndicatorBarStyle)
    visual_effect.addSubview_(progress_bar)

    # Add percentage label (white text)
    percent_label = NSTextField.labelWithString_(f"{percent}%")
    percent_label.setTextColor_(AppKit.NSColor.whiteColor())
    percent_label.setBackgroundColor_(AppKit.NSColor.clearColor())
    percent_label.setAlignment_(AppKit.NSCenterTextAlignment)
    percent_label.setFrame_(NSMakeRect(window_width - 60, 193, 50, 24))
    percent_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
    visual_effect.addSubview_(percent_label)

    # Move trophies row up
    y_img = 140   # was 80
    y_field = 110  # was 40

    trophy_types = ["platinum", "gold", "silver", "bronze"]
    num_trophies = len(trophy_types)
    img_size = 48
    margin = 30  # left/right margin
    available_width = window_width - 2 * margin
    spacing = (available_width - num_trophies * img_size) // (num_trophies - 1)
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

        # Edit field (hidden by default)
        trophy_field = UsernameEditField.alloc().init()
        trophy_field.setFrame_(NSMakeRect(x_offset, y_field, img_size, 24))
        trophy_field.setStringValue_(trophies.get(name, "0"))
        trophy_field.setHidden_(True)
        visual_effect.addSubview_(trophy_field)
        fields[name] = trophy_field

        # Label (shown by default)
        trophy_label = ClickableLabel.labelWithString_(trophies.get(name, "0"))
        trophy_label.setFrame_(NSMakeRect(x_offset, y_field, img_size, 24))
        trophy_label.setAlignment_(AppKit.NSCenterTextAlignment)
        trophy_label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        trophy_label.set_field_and_config(trophy_field, trophies)
        visual_effect.addSubview_(trophy_label)

        # Link label to field and field to label
        trophy_field.set_label_and_config(trophy_label, trophies)
        # Store the trophy name for saving
        trophy_field.trophy_name = name

        # Trophy name label (wider for "Platinum")
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
    icon_y = 240  # Adjust as needed to fit your layout
    level_icon_view = NSImageView.alloc().initWithFrame_(
        NSMakeRect(icon_x, icon_y, icon_size, icon_size)
    )
    level_icon_view.setImage_(level_icon)
    level_icon_view.setImageScaling_(AppKit.NSImageScaleProportionallyUpOrDown)
    visual_effect.addSubview_(level_icon_view)

    # Level label next to icon
    level_label = NSTextField.labelWithString_(f"Level {level}")
    level_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(18))
    level_label.setTextColor_(AppKit.NSColor.whiteColor())
    level_label.setBackgroundColor_(AppKit.NSColor.clearColor())
    level_label.setAlignment_(AppKit.NSLeftTextAlignment)
    level_label.setFrame_(NSMakeRect(
        icon_x + icon_size + 10, icon_y + 8, 120, 24))
    visual_effect.addSubview_(level_label)

    save_helper = SaveHelper.alloc().init()
    save_helper.setAll_((config, fields, trophies, window))
    delegate = WindowDelegate.alloc().initWithSaveHelper_(save_helper)
    window.setDelegate_(delegate)
    save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(160, 20, 100, 32))
    save_btn.setTitle_("Save")
    save_btn.setTarget_(save_helper)
    save_btn.setAction_("saveChanges:")
    visual_effect.addSubview_(save_btn)

    # When editing is finished (on Enter or focus lost), update label and hide field
    def end_editing(sender):
        new_name = sender.stringValue()
        username_label.setStringValue_(new_name)
        sender.setHidden_(True)
        username_label.setHidden_(False)
        config["username"] = new_name
        save_config(config)

    username_field.setTarget_(username_field)
    username_field.setAction_("endEditing:")
    # Patch the method to call our Python function

    def endEditing_(self, sender):
        end_editing(self)
    username_field.endEditing_ = endEditing_.__get__(
        username_field, NSTextField)

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


if __name__ == '__main__':
    open_native_window()

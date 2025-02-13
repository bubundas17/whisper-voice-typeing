import json

class Settings:
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            "hotkey": "f9",
            "hotkey_enabled": True,
            "input_device": None,
            "model": "large",
            "language": "auto"  # Add default language setting
        }
        self.load()

    def load(self):
        try:
            with open(self.settings_file, "r") as f:
                self._settings = json.load(f)
        except:
            self._settings = self.default_settings.copy()

    def save(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self._settings, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()

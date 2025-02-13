from PyQt5.QtWidgets import QWidget, QSystemTrayIcon, QMenu, QActionGroup, QDialog, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
import keyboard
import torch
import whisper
import pyautogui
import os 
from ..core.recording_thread import RecordingThread
from ..gui.recording_dialog import RecordingDialog
from ..utils.settings import Settings

LANGUAGES = {
    "auto": "Auto Detect",
    "hi": "Hindi",          # Moved to top for prominence
    "bn": "Bengali",        # Added Bengali
    "af": "Afrikaans", "ar": "Arabic", "hy": "Armenian", "az": "Azerbaijani", 
    "be": "Belarusian", "bs": "Bosnian", "bg": "Bulgarian", "ca": "Catalan", 
    "zh": "Chinese", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
    "en": "English", "et": "Estonian", "fi": "Finnish", "fr": "French", "gl": "Galician",
    "de": "German", "el": "Greek", "he": "Hebrew", "hu": "Hungarian",
    "is": "Icelandic", "id": "Indonesian", "it": "Italian", "ja": "Japanese", 
    "kk": "Kazakh", "ko": "Korean", "lv": "Latvian", "lt": "Lithuanian", "mk": "Macedonian",
    "ms": "Malay", "mr": "Marathi", "mi": "Maori", "ne": "Nepali", "no": "Norwegian",
    "fa": "Persian", "pl": "Polish", "pt": "Portuguese", "ro": "Romanian", "ru": "Russian",
    "sr": "Serbian", "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sw": "Swahili",
    "sv": "Swedish", "tl": "Tagalog", "ta": "Tamil", "th": "Thai", "tr": "Turkish",
    "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese", "cy": "Welsh"
}

class SystemTrayApp(QWidget):
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.init_variables()
        self.setup_gui()
        self.setup_recording()
        self.setup_hotkeys()
        self.toggle_signal.connect(self.toggle_recording)

    def init_variables(self):
        self.hotkey = self.settings.get("hotkey", "f9")
        self.hotkey_enabled = self.settings.get("hotkey_enabled", True)
        self.input_device = self.settings.get("input_device")
        self.model_name = self.settings.get("model", "large")
        self.is_recording = False
        self.recording_thread = None
        self.recording_dialog = None
        self.model = None
        self.selected_language = self.settings.get("language", "auto")

    def setup_gui(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("./ai-technology.png"))

        # Create and style the menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
            }
            QMenu::item {
                padding: 5px 30px 5px 30px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #34495e;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 5px 0px 5px 0px;
            }
        """)
        
        # Model selection submenu with icon
        model_menu = menu.addMenu("🔧 Select Model")
        model_menu.setStyleSheet(menu.styleSheet())
        model_group = QActionGroup(self)
        for model in ["tiny", "base", "small", "medium", "large"]:
            action = model_menu.addAction(model)
            action.setCheckable(True)
            action.setChecked(model == self.model_name)
            action.triggered.connect(lambda _, m=model: self.change_model(m))
            model_group.addAction(action)

        # Language selection submenu with icon
        language_menu = menu.addMenu("🌍 Select Language")
        language_menu.setStyleSheet(menu.styleSheet())
        language_group = QActionGroup(self)
        
        # Add frequently used languages first
        priority_langs = ["auto", "hi", "bn", "en"]
        for code in priority_langs:
            name = LANGUAGES[code]
            action = language_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(code == self.selected_language)
            action.setData(code)
            action.triggered.connect(lambda _, a=action: self.change_language(a.data()))
            language_group.addAction(action)
        
        # Add separator after priority languages
        language_menu.addSeparator()
        
        # Add remaining languages
        for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1]):
            if code not in priority_langs:
                action = language_menu.addAction(name)
                action.setCheckable(True)
                action.setChecked(code == self.selected_language)
                action.setData(code)
                action.triggered.connect(lambda _, a=action: self.change_language(a.data()))
                language_group.addAction(action)
        
        menu.addSeparator()
        
        # Add icons to other menu items
        self.toggle_hotkey_action = menu.addAction("⌨️ Disable Hotkey" if self.hotkey_enabled else "⌨️ Enable Hotkey")
        self.toggle_hotkey_action.triggered.connect(self.toggle_hotkey)
        
        self.change_hotkey_action = menu.addAction("🔑 Change Hotkey")
        self.change_hotkey_action.triggered.connect(self.change_hotkey)
        
        menu.addSeparator()
        self.exit_action = menu.addAction("❌ Exit")
        self.exit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def setup_recording(self):
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(self.model_name, device=device)
        except Exception as e:
            self.handle_error(f"Failed to load model: {str(e)}")

    def setup_hotkeys(self):
        if self.hotkey_enabled:
            keyboard.add_hotkey(self.hotkey, lambda: self.toggle_signal.emit())
        keyboard.add_hotkey("ctrl+x", self.quit_app)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        if not self.recording_dialog:
            self.recording_dialog = RecordingDialog(self.input_device, self.set_input_device)
            self.recording_dialog.close_signal.connect(self.stop_recording)

        self.recording_thread = RecordingThread(self.input_device)
        self.recording_thread.finished.connect(self.handle_result)
        self.recording_thread.error.connect(self.handle_error)
        self.recording_thread.status.connect(self.recording_dialog.update_status)
        self.recording_thread.audio_level_updated.connect(self.recording_dialog.update_audio_level)

        self.recording_dialog.show()
        self.recording_thread.start()

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.stop()
            self.recording_thread = None

        if self.recording_dialog:
            self.recording_dialog.hide()

    def handle_result(self, data):
        audio, wav_path = data
        if audio is None or len(audio) == 0 or not os.path.exists(wav_path):
            return

        try:
            result = self.model.transcribe(
                wav_path,
                language=None if self.selected_language == "auto" else self.selected_language,
                temperature=0.2,
                best_of=2,
                fp16=False
            )
            text = result["text"].strip().replace('\n', ' ')
            if text:
                pyautogui.typewrite(text)
        except Exception as e:
            self.handle_error(str(e))

    def toggle_hotkey(self):
        self.hotkey_enabled = not self.hotkey_enabled
        if self.hotkey_enabled:
            keyboard.add_hotkey(self.hotkey, lambda: self.toggle_signal.emit())
            self.toggle_hotkey_action.setText("Disable Hotkey")
        else:
            keyboard.remove_hotkey(self.hotkey)
            self.toggle_hotkey_action.setText("Enable Hotkey")
        
        self.settings.set("hotkey_enabled", self.hotkey_enabled)

    def change_hotkey(self):
        if self.is_recording:
            self.stop_recording()
        
        if self.hotkey_enabled:
            keyboard.remove_hotkey(self.hotkey)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Hotkey")
        layout = QVBoxLayout()
        label = QLabel("Press new hotkey...")
        layout.addWidget(label)
        dialog.setLayout(layout)
        
        def on_key(event):
            if event.event_type == keyboard.KEY_DOWN:
                self.hotkey = event.name
                if self.hotkey_enabled:
                    keyboard.add_hotkey(self.hotkey, lambda: self.toggle_signal.emit())
                self.settings.set("hotkey", self.hotkey)
                dialog.close()
                keyboard.unhook_all()
                self.setup_hotkeys()
        
        keyboard.hook(on_key)
        dialog.exec_()

    def change_model(self, model_name):
        self.model_name = model_name
        if self.is_recording:
            self.stop_recording()
        
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(self.model_name, device=device)
            self.settings.set("model", self.model_name)
        except Exception as e:
            self.handle_error(f"Failed to load model: {str(e)}")  # Fixed missing quotation mark

    def change_language(self, language_code):
        self.selected_language = language_code
        self.settings.set("language", language_code)
        print(f"Language changed to: {LANGUAGES[language_code]}")

    def set_input_device(self, device):
        self.input_device = device
        if self.is_recording:
            self.stop_recording()
            self.start_recording()
        self.settings.set("input_device", device)

    def handle_error(self, error_message):
        print(f"Error: {error_message}")
        if self.recording_dialog:
            self.recording_dialog.update_status(f"Error: {error_message}")

    def quit_app(self):
        self.stop_recording()
        if self.hotkey_enabled:
            keyboard.remove_hotkey(self.hotkey)
        keyboard.unhook_all()
        QApplication.quit()

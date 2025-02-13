import sys
import numpy as np
import sounddevice as sd
import whisper
import pyautogui
import keyboard
import json
import time
import wave
import os
import torch
from PyQt5.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QActionGroup,
    QProgressBar  # Added for audio level display
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon


class RecordingThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    audio_level_updated = pyqtSignal(float)  # New signal for audio level

    def __init__(self, input_device):
        super().__init__()
        self.input_device = input_device
        self.running = True
        self.silence_threshold = 0.02
        self.silence_duration = 1.0
        self.stream = None

    def run(self):
        try:
            self.status.emit("Listening...")
            print("Starting continuous audio capture...")
            
            self.stream = sd.InputStream(
                device=self.input_device,
                samplerate=16000,
                channels=1,
                dtype="float32"
            )
            self.stream.start()

            state = "IDLE"
            buffer = []
            last_voice_time = time.time()

            while self.running:
                data, _ = self.stream.read(4096)
                audio_level = np.abs(data).max()
                self.audio_level_updated.emit(audio_level)  # Emit audio level

                if state == "IDLE":
                    if audio_level > self.silence_threshold:
                        print("Speech detected, starting recording.")
                        self.status.emit("Recording...")
                        state = "RECORDING"
                        buffer = [data]
                        last_voice_time = time.time()
                elif state == "RECORDING":
                    buffer.append(data)
                    if audio_level > self.silence_threshold:
                        last_voice_time = time.time()
                    else:
                        if time.time() - last_voice_time >= self.silence_duration:
                            print("Silence detected, processing...")
                            self.status.emit("Processing...")
                            audio = np.concatenate(buffer, axis=0).astype(np.float32).flatten()
                            self.process_and_emit(audio)
                            state = "IDLE"
                            buffer = []
                            self.status.emit("Listening...")
        except Exception as e:
            print(f"Recording error: {str(e)}")
            self.error.emit(str(e))
        finally:
            if self.stream:
                self.stream.stop()
                self.stream.close()

    def process_and_emit(self, audio):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        debug_dir = "debug_audio"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        wav_path = os.path.join(debug_dir, f"recording_{timestamp}.wav")
        audio_int16 = (audio * 32767).astype(np.int16)
        
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"Saved debug audio to: {wav_path}")
        self.finished.emit((audio, wav_path))

    def stop(self):
        self.running = False
        self.wait()


class RecordingDialog(QDialog):
    close_signal = pyqtSignal()  # New signal for closing

    def __init__(self, current_device, device_changed_callback):
        super().__init__()
        self.setWindowTitle("Speech to Text")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; border: 2px solid #34495e; border-radius: 10px; }
            QLabel { color: #ecf0f1; font-size: 16px; }
            QComboBox { color: #ecf0f1; background-color: #34495e; }
            QComboBox QAbstractItemView { color: #ecf0f1; background-color: #2c3e50; }
            QProgressBar { 
                height: 20px;
                text-align: center;
                border: 1px solid #34495e;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
            }
        """)
        self.device_changed_callback = device_changed_callback

        layout = QVBoxLayout()
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Audio level display
        self.audio_level = QProgressBar()
        self.audio_level.setRange(0, 100)
        self.audio_level.setFormat("%p%")
        layout.addWidget(self.audio_level)

        # Device selection
        self.devices = [(idx, dev) for idx, dev in enumerate(sd.query_devices()) 
                       if dev['max_input_channels'] > 0]
        self.mic_combo = QComboBox()
        for idx, dev in self.devices:
            self.mic_combo.addItem(f"{idx}: {dev['name']}", idx)
        if current_device is not None:
            self.set_device_selection(current_device)
        layout.addWidget(self.mic_combo)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_signal.emit)  # Emit close signal
        layout.addWidget(self.close_button)

        self.mic_combo.currentIndexChanged.connect(self.on_device_changed)
        self.setLayout(layout)
        self.setFixedSize(300, 180)

        # Center dialog
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - self.width()//2, screen.center().y() - self.height()//2)

    def set_device_selection(self, device):
        for i in range(self.mic_combo.count()):
            if self.mic_combo.itemData(i) == device:
                self.mic_combo.setCurrentIndex(i)
                break

    def update_status(self, status):
        self.status_label.setText(status)

    def update_audio_level(self, level):
        # Convert audio level (0.0-1.0) to percentage
        percent = min(int(level * 200), 100)  # Scale to make 0.5 = 100%
        self.audio_level.setValue(percent)

    def on_device_changed(self, index):
        new_device = self.mic_combo.itemData(index)
        self.device_changed_callback(new_device)


class SystemTrayApp(QWidget):
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_variables()
        self.setup_gui()
        self.setup_recording()
        self.setup_hotkeys()
        self.toggle_signal.connect(self.toggle_recording)

    def init_variables(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.hotkey = settings.get("hotkey", "f9")
                self.hotkey_enabled = settings.get("hotkey_enabled", True)
                device = settings.get("input_device", None)
                self.model_name = settings.get("model", "small")
                self.input_device = int(device) if device is not None else None
        except:
            self.hotkey = "f9"
            self.hotkey_enabled = True
            self.input_device = None
            self.model_name = "small"

        self.is_recording = False
        self.recording_thread = None
        self.recording_dialog = None
        self.model = None

    def setup_gui(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("./ai-technology.png"))

        menu = QMenu()
        model_menu = menu.addMenu("Select Model")
        model_group = QActionGroup(self)
        for model in ["tiny", "base", "small", "medium", "large"]:
            action = model_menu.addAction(model)
            action.setCheckable(True)
            action.setChecked(model == self.model_name)
            action.triggered.connect(lambda _, m=model: self.change_model(m))
            model_group.addAction(action)
        
        menu.addSeparator()
        self.toggle_hotkey_action = menu.addAction("Disable Hotkey" if self.hotkey_enabled else "Enable Hotkey")
        self.toggle_hotkey_action.triggered.connect(self.toggle_hotkey)
        self.change_hotkey_action = menu.addAction("Change Hotkey")
        self.change_hotkey_action.triggered.connect(self.change_hotkey)
        self.exit_action = menu.addAction("Exit")
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
                language="en",
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
        
        # Save settings
        self.save_settings()

    def change_hotkey(self):
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Remove existing hotkey
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
                self.save_settings()
                dialog.close()
                keyboard.unhook_all()
                # Re-setup original hotkeys
                self.setup_hotkeys()
        
        keyboard.hook(on_key)
        dialog.exec_()

    def change_model(self, model_name):
        self.model_name = model_name
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Reload model
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(self.model_name, device=device)
        except Exception as e:
            self.handle_error(f"Failed to load model: {str(e)}")
        
        self.save_settings()

    def set_input_device(self, device):
        self.input_device = device
        if self.is_recording:
            self.stop_recording()
            self.start_recording()
        self.save_settings()

    def save_settings(self):
        settings = {
            "hotkey": self.hotkey,
            "hotkey_enabled": self.hotkey_enabled,
            "input_device": self.input_device,
            "model": self.model_name
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            self.handle_error(f"Failed to save settings: {str(e)}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray_app = SystemTrayApp()
    sys.exit(app.exec_())
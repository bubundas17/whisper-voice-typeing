import sounddevice as sd
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QComboBox, QPushButton, QProgressBar, QApplication
from PyQt5.QtCore import Qt, pyqtSignal

class RecordingDialog(QDialog):
    close_signal = pyqtSignal()

    def __init__(self, current_device, device_changed_callback):
        super().__init__()
        self.setWindowTitle("Speech to Text")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self._setup_ui()
        self.device_changed_callback = device_changed_callback
        self._initialize_devices(current_device)

    def _setup_ui(self):
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
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.audio_level = QProgressBar()
        self.audio_level.setRange(0, 100)
        self.audio_level.setFormat("%p%")
        layout.addWidget(self.audio_level)

        self.mic_combo = QComboBox()
        layout.addWidget(self.mic_combo)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_signal.emit)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.setFixedSize(300, 180)

        # Center dialog
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - self.width()//2, screen.center().y() - self.height()//2)

    def _initialize_devices(self, current_device):
        self.devices = [(idx, dev) for idx, dev in enumerate(sd.query_devices()) 
                       if dev['max_input_channels'] > 0]
        for idx, dev in self.devices:
            self.mic_combo.addItem(f"{idx}: {dev['name']}", idx)
        
        if current_device is not None:
            self.set_device_selection(current_device)
            
        self.mic_combo.currentIndexChanged.connect(self.on_device_changed)

    def set_device_selection(self, device):
        for i in range(self.mic_combo.count()):
            if self.mic_combo.itemData(i) == device:
                self.mic_combo.setCurrentIndex(i)
                break

    def update_status(self, status):
        self.status_label.setText(status)

    def update_audio_level(self, level):
        # Adjust scaling for better visualization
        # RMS values are typically much smaller, so we scale them up
        percent = min(int(level * 1000), 100)  # Increased scaling factor
        self.audio_level.setValue(percent)

    def on_device_changed(self, index):
        new_device = self.mic_combo.itemData(index)
        self.device_changed_callback(new_device)

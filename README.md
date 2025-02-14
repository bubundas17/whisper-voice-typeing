# Whisper SST (Speech-to-Text)

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/bubundas17/whisper-voice-typeing.svg?style=flat&logo=github)](https://github.com/bubundas17/whisper-voice-typeing/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/bubundas17/whisper-voice-typeing.svg?style=flat&logo=github)](https://github.com/bubundas17/whisper-voice-typeing/network)
[![GitHub issues](https://img.shields.io/github/issues/bubundas17/whisper-voice-typeing.svg?style=flat&logo=github)](https://github.com/bubundas17/whisper-voice-typeing/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/bubundas17/whisper-voice-typeing.svg?style=flat&logo=github)](https://github.com/bubundas17/whisper-voice-typeing/pulls)
[![License](https://img.shields.io/github/license/bubundas17/whisper-voice-typeing.svg?style=flat&logo=opensourceinitiative)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python)](https://www.python.org)
[![PyQt5](https://img.shields.io/badge/PyQt-5-green?logo=qt)](https://www.qt.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper-orange?logo=openai)](https://openai.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful system tray application for real-time speech-to-text conversion using OpenAI's Whisper model.

[Features](#features) • [Requirements](#requirements) • [Installation](#installation) • [Usage](#usage) • [Configuration](#configuration) • [Contributing](#contributing) • [License](#license)

</div>

## ✨ Features

- 🎤 **Real-time Conversion**: Instant speech-to-text with minimal delay
- 🌍 **Multilingual Support**: Works with 50+ languages including Hindi and Bengali
- ⚡ **GPU Acceleration**: CUDA support for faster processing
- 🎯 **Smart Detection**: Automatic language detection
- ⌨️ **Customizable**: Configurable keyboard shortcuts
- 🎛️ **Flexible Models**: Choose from tiny to large Whisper models
- 💻 **System Integration**: Clean system tray interface
- 🎚️ **Visual Feedback**: Real-time audio level visualization
- 🎙️ **Device Support**: Works with multiple input devices

## 🔧 Requirements

### System Requirements
- Python 3.8 or higher
- CUDA-compatible GPU (optional, for GPU acceleration)
- Windows/Linux/macOS

### Dependencies
- PyQt5
- OpenAI Whisper
- PyAudio
- torch
- numpy
- keyboard

## 🚀 Installation & Usage

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/bubundas17/whisper-voice-typeing.git
   cd whisper-voice-typeing
   ```

2. **Run the application**
   
   **Windows users:**
   ```bash
   run.bat
   ```
   
   **Linux/macOS users:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

The run scripts will automatically:
- Update the project from git
- Create and activate a virtual environment
- Install/update all dependencies
- Install PyTorch with CUDA support if a GPU is available
- Start the application

### Manual Installation

If you prefer to install manually, follow these steps:

1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install PyTorch (with CUDA support if available):
   ```bash
   # For CUDA 11.8
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

4. Start the application:
   ```bash
   python run.py
   ```

## 💻 Basic Usage

2. **Access from system tray**
   - Look for the Whisper SST icon in your system tray
   - Right-click to access settings and controls
   - Default hotkey is F9 to start/stop recording

## ⚙️ Configuration

The application can be configured through the settings menu or by editing `settings.json`:

```json
{
    "hotkey": "f9",
    "hotkey_enabled": true,
    "input_device": null,
    "model": "large",
    "language": "auto"
}
```

### Available Settings
- `hotkey`: Keyboard shortcut for start/stop recording
- `hotkey_enabled`: Enable/disable global hotkey
- `input_device`: Specify audio input device (null for default)
- `model`: Whisper model size ("tiny", "base", "small", "medium", "large")
- `language`: Target language ("auto" for automatic detection)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the amazing speech recognition model
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework

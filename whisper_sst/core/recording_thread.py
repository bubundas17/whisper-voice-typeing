import numpy as np
import sounddevice as sd
import wave
import time
import os
from PyQt5.QtCore import QThread, pyqtSignal

class RecordingThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    audio_level_updated = pyqtSignal(float)

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
                dtype="float32",
                callback=self._audio_callback,  # Add callback
                blocksize=1024  # Smaller blocksize for more frequent updates
            )
            self.stream.start()

            # Keep thread alive while running
            while self.running:
                time.sleep(0.1)  # Reduce CPU usage

        except Exception as e:
            print(f"Recording error: {str(e)}")
            self.error.emit(str(e))
        finally:
            if self.stream:
                self.stream.stop()
                self.stream.close()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        
        # Calculate RMS value for better level visualization
        audio_level = np.sqrt(np.mean(indata**2))
        self.audio_level_updated.emit(audio_level)

        # Store audio for speech detection
        if not hasattr(self, 'audio_buffer'):
            self.audio_buffer = []
        
        self.audio_buffer.append(indata.copy())
        
        # Check for speech and process
        self._process_audio()

    def _process_audio(self):
        if not hasattr(self, 'audio_buffer'):
            return

        # Convert buffer to numpy array
        audio = np.concatenate(self.audio_buffer)
        audio_level = np.sqrt(np.mean(audio**2))

        if audio_level > self.silence_threshold:
            if not hasattr(self, 'recording_buffer'):
                print("Speech detected, starting recording.")
                self.status.emit("Recording...")
                self.recording_buffer = []
            
            self.recording_buffer.extend(self.audio_buffer)
            self.last_voice_time = time.time()
        elif hasattr(self, 'recording_buffer'):
            if time.time() - self.last_voice_time >= self.silence_duration:
                print("Silence detected, processing...")
                self.status.emit("Processing...")
                audio = np.concatenate(self.recording_buffer)
                self.process_and_emit(audio)
                delattr(self, 'recording_buffer')
                self.status.emit("Listening...")

        # Clear the input buffer
        self.audio_buffer = []

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

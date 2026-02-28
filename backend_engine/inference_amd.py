"""
AMD Inference Engine (Windows Only)
Real-time deepfake audio detection using ONNX Runtime with DirectML acceleration.

IMPORTANT: This script is designed to run on Windows with AMD GPU.
It uses DirectML for GPU acceleration and PyAudio for microphone input.
"""

import os
import sys
import numpy as np
import threading
import time
from collections import deque

# Audio processing
try:
    import pyaudio
except ImportError:
    raise ImportError("PyAudio not installed. Install with: pip install pyaudio")

# ONNX Runtime with DirectML
try:
    import onnxruntime as ort
except ImportError:
    raise ImportError("ONNX Runtime not installed. Install with: pip install onnxruntime-directml")

# Audio preprocessing (same as training)
try:
    import librosa
    import scipy.signal
except ImportError:
    raise ImportError("librosa or scipy not installed. Install with: pip install librosa scipy")


class AudioPreprocessor:
    """
    Preprocesses audio chunks into Mel-Spectrograms for model input.
    """
    
    def __init__(self, target_sr=16000, duration=4.0, n_mels=224):
        self.target_sr = target_sr
        self.duration = duration
        self.target_length = int(target_sr * duration)
        self.n_mels = n_mels
    
    def preprocess(self, audio_chunk):
        """
        Convert audio chunk to Mel-Spectrogram.
        
        Args:
            audio_chunk (np.ndarray): Raw audio samples
            
        Returns:
            np.ndarray: Mel-Spectrogram of shape (1, 1, 224, 224)
        """
        # Ensure correct length
        if len(audio_chunk) < self.target_length:
            # Pad with zeros
            audio_chunk = np.pad(audio_chunk, (0, self.target_length - len(audio_chunk)))
        elif len(audio_chunk) > self.target_length:
            # Trim
            audio_chunk = audio_chunk[:self.target_length]
        
        # Generate Mel-Spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=audio_chunk,
            sr=self.target_sr,
            n_fft=2048,
            hop_length=512,
            n_mels=self.n_mels,
            fmin=0,
            fmax=self.target_sr // 2
        )
        
        # Convert to dB scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Resize to 224x224
        from scipy.ndimage import zoom
        
        # Calculate zoom factors
        zoom_factors = (224 / mel_spec_db.shape[0], 224 / mel_spec_db.shape[1])
        mel_spec_resized = zoom(mel_spec_db, zoom_factors, order=1)
        
        # Normalize to [0, 1]
        mel_spec_normalized = (mel_spec_resized - mel_spec_resized.min()) / (
            mel_spec_resized.max() - mel_spec_resized.min() + 1e-8
        )
        
        # Add batch and channel dimensions: (1, 1, 224, 224)
        mel_spec_final = mel_spec_normalized[np.newaxis, np.newaxis, :, :]
        
        return mel_spec_final.astype(np.float32)


class DeepGuardInference:
    """
    Real-time deepfake detection inference engine.
    """
    
    def __init__(self, model_path, use_gpu=True):
        """
        Initialize inference engine.
        
        Args:
            model_path (str): Path to ONNX model
            use_gpu (bool): Use DirectML GPU acceleration
        """
        self.model_path = model_path
        self.preprocessor = AudioPreprocessor()
        
        # Initialize ONNX Runtime session
        print("Initializing ONNX Runtime...")
        
        if use_gpu:
            # Use DirectML for AMD GPU acceleration
            providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
            print("Using DirectML (AMD GPU) acceleration")
        else:
            providers = ['CPUExecutionProvider']
            print("Using CPU inference")
        
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
            print(f"✓ Model loaded from {model_path}")
            
            # Print provider info
            print(f"Active providers: {self.session.get_providers()}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)
        
        # Get input/output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
    
    def predict(self, audio_chunk):
        """
        Predict trust score for audio chunk.
        
        Args:
            audio_chunk (np.ndarray): Raw audio samples
            
        Returns:
            float: Trust score (0-100), where higher = more likely real
        """
        # Preprocess
        spectrogram = self.preprocessor.preprocess(audio_chunk)
        
        # Run inference
        output = self.session.run([self.output_name], {self.input_name: spectrogram})
        
        # Convert logit to probability using sigmoid
        logit = output[0][0][0]
        probability = 1 / (1 + np.exp(-logit))
        
        # Convert to trust score (0-100)
        trust_score = probability * 100
        
        return trust_score


class AudioCapture:
    """
    Captures audio from system microphone in real-time.
    """
    
    def __init__(self, sample_rate=16000, chunk_duration=4.0, callback=None):
        """
        Initialize audio capture.
        
        Args:
            sample_rate (int): Sample rate in Hz
            chunk_duration (float): Duration of each chunk in seconds
            callback (callable): Function to call with each audio chunk
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.callback = callback
        
        # Rolling buffer for continuous capture
        self.buffer = deque(maxlen=self.chunk_size)
        
        # PyAudio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio callback for audio input.
        """
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Add to buffer
        self.buffer.extend(audio_data)
        
        # If buffer is full, process chunk
        if len(self.buffer) >= self.chunk_size:
            chunk = np.array(list(self.buffer))
            
            # Call user callback
            if self.callback:
                self.callback(chunk)
        
        return (in_data, pyaudio.paContinue)
    
    def start(self):
        """
        Start audio capture.
        """
        print("Starting audio capture...")
        
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self._audio_callback
        )
        
        self.is_running = True
        self.stream.start_stream()
        print("✓ Audio capture started")
    
    def stop(self):
        """
        Stop audio capture.
        """
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        self.audio.terminate()
        self.is_running = False
        print("Audio capture stopped")


def main():
    """
    Main inference loop.
    """
    print("=" * 60)
    print("DeepGuard Real-Time Inference (AMD Edition)")
    print("=" * 60)
    
    # Model path
    model_path = os.path.join('models', 'deepguard_amd.onnx')
    
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        print("Please export the model using export_onnx.py first")
        sys.exit(1)
    
    # Initialize inference engine
    inference = DeepGuardInference(model_path, use_gpu=True)
    
    # Callback for audio chunks
    def on_audio_chunk(chunk):
        """Process audio chunk and print trust score."""
        trust_score = inference.predict(chunk)
        
        # Color-coded output
        if trust_score >= 80:
            status = "✓ REAL"
            color = "\033[92m"  # Green
        elif trust_score >= 50:
            status = "⚠ UNCERTAIN"
            color = "\033[93m"  # Yellow
        else:
            status = "✗ DEEPFAKE"
            color = "\033[91m"  # Red
        
        reset = "\033[0m"
        
        print(f"{color}Trust Score: {trust_score:.1f}% - {status}{reset}")
    
    # Start audio capture
    capture = AudioCapture(callback=on_audio_chunk)
    
    try:
        capture.start()
        
        print("\nListening to microphone... (Press Ctrl+C to stop)")
        print("-" * 60)
        
        # Keep running
        while True:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        capture.stop()
        print("\n" + "=" * 60)
        print("Inference stopped")
        print("=" * 60)


if __name__ == '__main__':
    main()

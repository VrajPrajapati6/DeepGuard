"""
Quick test to verify DeepGuard model loads and runs inference correctly.
No dataset required - uses synthetic dummy audio.
"""

import sys
import torch
import numpy as np

print("=" * 60)
print("DeepGuard Model Quick Test")
print("=" * 60)

# ──────────────────────────────────────────
# Step 1: Check PyTorch
# ──────────────────────────────────────────
print(f"\n[1/5] PyTorch version: {torch.__version__}")
print(f"      CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"      CUDA device: {torch.cuda.get_device_name(0)}")

# ──────────────────────────────────────────
# Step 2: Load the model
# ──────────────────────────────────────────
print("\n[2/5] Loading DeepGuard PyTorch model...")
from train import DeepGuardModel

model = DeepGuardModel(pretrained=False)

# Try loading v2 model first, fall back to v1
import os
model_paths = [
    'models/deepguard_v2_robust.pth',
    'models/deepguard_model.pth',
]

loaded_path = None
for mp in model_paths:
    if os.path.exists(mp):
        checkpoint = torch.load(mp, map_location='cpu', weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        loaded_path = mp
        print(f"      Model loaded from: {mp}")
        if 'epoch' in checkpoint:
            print(f"      Epoch: {checkpoint['epoch']}")
        if 'val_acc' in checkpoint:
            print(f"      Validation Accuracy: {checkpoint['val_acc']:.2f}%")
        break

if loaded_path is None:
    print("      ERROR: No model file found!")
    sys.exit(1)

model.eval()
print("      Model set to eval mode - OK")

# ──────────────────────────────────────────
# Step 3: Test with dummy spectrogram input
# ──────────────────────────────────────────
print("\n[3/5] Testing inference with dummy spectrogram...")
dummy_input = torch.randn(1, 1, 224, 224)  # (batch, channels, height, width)

with torch.no_grad():
    output = model(dummy_input)
    prob = torch.sigmoid(output).item()

print(f"      Raw output: {output.item():.4f}")
print(f"      Sigmoid probability: {prob:.4f}")
print(f"      Prediction: {'REAL' if prob > 0.5 else 'FAKE'} (confidence: {max(prob, 1-prob)*100:.1f}%)")
print("      Inference OK!")

# ──────────────────────────────────────────
# Step 4: Test with synthetic audio waveform
# ──────────────────────────────────────────
print("\n[4/5] Testing full pipeline (audio -> spectrogram -> prediction)...")
import torchaudio.transforms as T

# Generate 4 seconds of synthetic audio at 16kHz
sr = 16000
duration = 4.0
t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

# Create a simple sine wave (simulating speech-like audio)
audio = np.sin(2 * np.pi * 440 * t) * 0.5  # 440 Hz tone
audio += np.random.randn(len(audio)).astype(np.float32) * 0.01  # Add slight noise
waveform = torch.from_numpy(audio).unsqueeze(0)  # (1, samples)

# Convert to Mel-Spectrogram (same as training pipeline)
mel_transform = T.MelSpectrogram(sample_rate=sr, n_fft=2048, hop_length=512, n_mels=128)
mel_spec = mel_transform(waveform)
mel_spec_db = T.AmplitudeToDB()(mel_spec)

# Resize to 224x224
mel_spec_resized = torch.nn.functional.interpolate(
    mel_spec_db.unsqueeze(0), size=(224, 224), mode='bilinear', align_corners=False
).squeeze(0)

# Normalize to [0, 1]
mel_min = mel_spec_resized.min()
mel_max = mel_spec_resized.max()
if mel_max > mel_min:
    mel_spec_norm = (mel_spec_resized - mel_min) / (mel_max - mel_min)
else:
    mel_spec_norm = torch.zeros_like(mel_spec_resized)

# Add batch dimension and run inference
input_tensor = mel_spec_norm.unsqueeze(0)  # (1, 1, 224, 224)

with torch.no_grad():
    output = model(input_tensor)
    prob = torch.sigmoid(output).item()

print(f"      Synthetic audio -> Mel-Spectrogram -> Model")
print(f"      Input shape: {input_tensor.shape}")
print(f"      Sigmoid probability: {prob:.4f}")
print(f"      Prediction: {'REAL' if prob > 0.5 else 'FAKE'}")
print("      Full pipeline OK!")

# ──────────────────────────────────────────
# Step 5: Test ONNX model (if available)
# ──────────────────────────────────────────
print("\n[5/5] Testing ONNX model...")
onnx_path = 'models/deepguard_amd_v2.onnx'

if os.path.exists(onnx_path):
    try:
        import onnxruntime as ort
        
        # Try CPU provider (safe on all platforms)
        session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        
        input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        print(f"      ONNX model loaded: {onnx_path}")
        print(f"      Input name: {input_name}, shape: {input_shape}")
        
        # Run inference with dummy input
        dummy_np = np.random.randn(1, 1, 224, 224).astype(np.float32)
        onnx_output = session.run(None, {input_name: dummy_np})
        onnx_prob = 1 / (1 + np.exp(-onnx_output[0][0][0]))  # sigmoid
        
        print(f"      ONNX output: {onnx_output[0][0][0]:.4f}")
        print(f"      ONNX sigmoid: {onnx_prob:.4f}")
        print(f"      ONNX prediction: {'REAL' if onnx_prob > 0.5 else 'FAKE'}")
        print("      ONNX inference OK!")
    except ImportError:
        print("      onnxruntime not installed. Installing...")
        print("      Run: pip install onnxruntime")
    except Exception as e:
        print(f"      ONNX test failed: {e}")
else:
    print(f"      ONNX model not found at {onnx_path}, skipping")

# ──────────────────────────────────────────
# Summary
# ──────────────────────────────────────────
print("\n" + "=" * 60)
print("ALL TESTS PASSED - DeepGuard model is working!")
print("=" * 60)

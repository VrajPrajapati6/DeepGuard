"""
Test script for DeepGuard v2 model on Mac
Tests the fine-tuned model on sample audio files to verify it works correctly.
"""

import os
import argparse
import torch
import torchaudio
import torchaudio.transforms as T
from train import DeepGuardModel, get_device
import random


def load_model(model_path, device):
    """
    Load the fine-tuned model.
    
    Args:
        model_path: Path to model checkpoint
        device: Device to load model on
        
    Returns:
        Loaded model
    """
    print(f"Loading model from {model_path}...")
    
    # Create model
    model = DeepGuardModel(pretrained=False)
    
    # Load weights
    checkpoint = torch.load(model_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    print(f"✓ Model loaded successfully")
    print(f"  Epoch: {checkpoint['epoch']}")
    print(f"  Validation Accuracy: {checkpoint['val_acc']:.2f}%")
    
    return model


def preprocess_audio(audio_path, target_sr=16000, duration=4.0, device='cpu'):
    """
    Preprocess audio file to model input format.
    Same preprocessing as training.
    
    Args:
        audio_path: Path to audio file
        target_sr: Target sample rate
        duration: Target duration in seconds
        device: Device to load tensor on
        
    Returns:
        Preprocessed spectrogram tensor (1, 1, 224, 224)
    """
    # Load audio
    try:
        import soundfile as sf
        waveform_np, sr = sf.read(audio_path, dtype='float32')
        waveform = torch.from_numpy(waveform_np).unsqueeze(0)
        
        # Convert to mono if stereo
        if len(waveform_np.shape) > 1 and waveform_np.shape[1] > 1:
            waveform = torch.from_numpy(waveform_np.mean(axis=1)).unsqueeze(0)
    except:
        waveform, sr = torchaudio.load(audio_path)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
    
    # Resample if necessary
    if sr != target_sr:
        resampler = T.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)
    
    # Pad or trim to target length
    target_length = int(target_sr * duration)
    if waveform.shape[1] < target_length:
        padding = target_length - waveform.shape[1]
        waveform = torch.nn.functional.pad(waveform, (0, padding))
    elif waveform.shape[1] > target_length:
        # Center crop
        start = (waveform.shape[1] - target_length) // 2
        waveform = waveform[:, start:start + target_length]
    
    # Generate Mel-Spectrogram
    mel_spectrogram = T.MelSpectrogram(
        sample_rate=target_sr,
        n_fft=2048,
        hop_length=512,
        n_mels=128
    )
    
    mel_spec = mel_spectrogram(waveform)
    mel_spec_db = T.AmplitudeToDB()(mel_spec)
    
    # Resize to 224x224
    resize = torch.nn.functional.interpolate(
        mel_spec_db.unsqueeze(0),
        size=(224, 224),
        mode='bilinear',
        align_corners=False
    )
    mel_spec_resized = resize.squeeze(0)
    
    # Normalize to [0, 1]
    mel_spec_min = mel_spec_resized.min()
    mel_spec_max = mel_spec_resized.max()
    
    if mel_spec_max > mel_spec_min:
        mel_spec_normalized = (mel_spec_resized - mel_spec_min) / (mel_spec_max - mel_spec_min)
    else:
        mel_spec_normalized = torch.zeros_like(mel_spec_resized)
    
    # Add batch dimension and move to device
    return mel_spec_normalized.unsqueeze(0).to(device)


def predict(model, audio_path, device):
    """
    Make prediction on a single audio file.
    
    Args:
        model: Loaded model
        audio_path: Path to audio file
        device: Device to run inference on
        
    Returns:
        tuple: (prediction, confidence, label)
    """
    # Preprocess
    spectrogram = preprocess_audio(audio_path, device=device)
    
    # Inference
    with torch.no_grad():
        output = model(spectrogram)
        probability = torch.sigmoid(output).item()
    
    # Interpret result
    # probability > 0.5 = Real (bona-fide)
    # probability < 0.5 = Fake (spoof)
    is_real = probability > 0.5
    confidence = probability if is_real else (1 - probability)
    label = "REAL" if is_real else "FAKE"
    
    return is_real, confidence, label


def test_on_dataset_samples(model, data_dir, device, num_samples=10):
    """
    Test model on random samples from the In-the-Wild dataset.
    
    Args:
        model: Loaded model
        data_dir: Path to dataset directory
        device: Device to run inference on
        num_samples: Number of samples to test
    """
    import csv
    
    print(f"\n{'='*60}")
    print(f"Testing on {num_samples} random samples from dataset")
    print(f"{'='*60}\n")
    
    # Read metadata
    meta_file = os.path.join(data_dir, 'meta.csv')
    samples = []
    
    with open(meta_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append((row['file'], row['label'], row['speaker']))
    
    # Random sample
    test_samples = random.sample(samples, min(num_samples, len(samples)))
    
    correct = 0
    total = 0
    
    for filename, true_label, speaker in test_samples:
        audio_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(audio_path):
            print(f"⚠ File not found: {filename}")
            continue
        
        # Predict
        is_real, confidence, pred_label = predict(model, audio_path, device)
        
        # Ground truth
        true_is_real = (true_label == 'bona-fide')
        true_label_str = "REAL" if true_is_real else "FAKE"
        
        # Check correctness
        is_correct = (is_real == true_is_real)
        correct += int(is_correct)
        total += 1
        
        # Display result
        status = "✓" if is_correct else "✗"
        print(f"{status} {filename:15s} | Speaker: {speaker:20s}")
        print(f"  Predicted: {pred_label:4s} ({confidence*100:.1f}% confidence)")
        print(f"  Actual:    {true_label_str:4s}")
        print()
    
    # Summary
    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"{'='*60}")
    print(f"Test Results: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    print(f"{'='*60}\n")


def test_on_custom_file(model, audio_path, device):
    """
    Test model on a custom audio file.
    
    Args:
        model: Loaded model
        audio_path: Path to audio file
        device: Device to run inference on
    """
    print(f"\n{'='*60}")
    print(f"Testing on custom file: {audio_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(audio_path):
        print(f"✗ File not found: {audio_path}")
        return
    
    # Predict
    is_real, confidence, label = predict(model, audio_path, device)
    
    # Display result
    print(f"Prediction: {label}")
    print(f"Confidence: {confidence*100:.1f}%")
    print(f"\nInterpretation:")
    if is_real:
        print(f"  → This audio is likely AUTHENTIC/REAL human speech")
    else:
        print(f"  → This audio is likely a DEEPFAKE/SYNTHETIC voice")
    print()


def main(args):
    """
    Main testing function.
    """
    print("=" * 60)
    print("DeepGuard v2 Model Testing")
    print("=" * 60)
    
    # Set device
    device = get_device()
    
    # Load model
    model = load_model(args.model_path, device)
    
    # Test on dataset samples
    if args.test_dataset:
        test_on_dataset_samples(
            model, 
            args.data_dir, 
            device, 
            num_samples=args.num_samples
        )
    
    # Test on custom file
    if args.audio_file:
        test_on_custom_file(model, args.audio_file, device)
    
    print("Testing complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test DeepGuard v2 model')
    
    parser.add_argument('--model-path', type=str, default='models/deepguard_v2_robust.pth',
                        help='Path to model checkpoint')
    parser.add_argument('--data-dir', type=str, default='data/release_in_the_wild',
                        help='Path to In-the-Wild dataset directory')
    parser.add_argument('--test-dataset', action='store_true',
                        help='Test on random samples from dataset')
    parser.add_argument('--num-samples', type=int, default=10,
                        help='Number of random samples to test')
    parser.add_argument('--audio-file', type=str,
                        help='Path to custom audio file to test')
    
    args = parser.parse_args()
    
    # Default: test on dataset if no custom file specified
    if not args.audio_file:
        args.test_dataset = True
    
    main(args)

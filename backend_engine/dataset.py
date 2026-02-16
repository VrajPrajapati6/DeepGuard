"""
DeepGuard Dataset Loader for ASVspoof 2019 LA
Loads audio files, generates Mel-Spectrograms, and provides labels for training.
"""

import os
import torch
import torchaudio
import torchaudio.transforms as T
from torch.utils.data import Dataset
import numpy as np


class ASVspoofDataset(Dataset):
    """
    Custom Dataset for ASVspoof 2019 Logical Access (LA) dataset.
    
    Converts audio files to Mel-Spectrograms for MobileNetV2 input.
    """
    
    def __init__(self, data_dir, protocol_file, subset='train', target_sr=16000, duration=4.0):
        """
        Args:
            data_dir (str): Path to ASVspoof2019_LA_train/dev/eval directory
            protocol_file (str): Path to protocol file (e.g., ASVspoof2019_LA_cm_protocols/ASVspoof2019.LA.cm.train.trn.txt)
            subset (str): 'train', 'dev', or 'eval'
            target_sr (int): Target sample rate (default: 16000 Hz)
            duration (float): Target audio duration in seconds (default: 4.0)
        """
        self.data_dir = data_dir
        self.subset = subset
        self.target_sr = target_sr
        self.duration = duration
        self.target_length = int(target_sr * duration)
        
        # Parse protocol file
        self.samples = self._parse_protocol(protocol_file)
        
        # Mel-Spectrogram transform
        self.mel_spectrogram = T.MelSpectrogram(
            sample_rate=target_sr,
            n_fft=2048,
            hop_length=512,
            n_mels=224,  # Height for MobileNetV2
            f_min=0,
            f_max=target_sr // 2
        )
        
        # Amplitude to dB conversion
        self.amplitude_to_db = T.AmplitudeToDB(stype='power', top_db=80)
        
    def _parse_protocol(self, protocol_file):
        """
        Parse ASVspoof protocol file.
        
        Format: SPEAKER_ID AUDIO_FILE_NAME - ATTACK_TYPE LABEL
        Example: LA_0079 LA_T_1138215 - - bonafide
        
        Returns:
            List of tuples: (audio_filename, label)
            label: 1 for bonafide (real), 0 for spoof (fake)
        """
        samples = []
        
        with open(protocol_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                
                audio_filename = parts[1] + '.flac'
                label_str = parts[4]
                
                
                label = 1 if label_str == 'bonafide' else 0
                
                samples.append((audio_filename, label))
        
        return samples
    
    def _load_audio(self, audio_path):
        """
        Load audio file and preprocess to fixed length.
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            torch.Tensor: Preprocessed audio waveform
        """
        # Load audio with soundfile (avoids torchcodec dependency)
        import soundfile as sf
        waveform_np, sr = sf.read(audio_path, dtype='float32')
        
        # Convert to torch tensor and add channel dimension
        waveform = torch.from_numpy(waveform_np).unsqueeze(0)  # (1, samples)
        
        # Convert to mono if stereo (soundfile returns (samples,) for mono, (samples, channels) for stereo)
        if len(waveform_np.shape) > 1 and waveform_np.shape[1] > 1:
            waveform = torch.from_numpy(waveform_np.mean(axis=1)).unsqueeze(0)
        
        # Resample if necessary
        if sr != self.target_sr:
            resampler = T.Resample(orig_freq=sr, new_freq=self.target_sr)
            waveform = resampler(waveform)
        
        # Pad or trim to target length
        current_length = waveform.shape[1]
        
        if current_length < self.target_length:
            # Pad with zeros
            padding = self.target_length - current_length
            waveform = torch.nn.functional.pad(waveform, (0, padding))
        elif current_length > self.target_length:
            # Trim to target length
            waveform = waveform[:, :self.target_length]
        
        return waveform
    
    def _generate_spectrogram(self, waveform):
        """
        Generate Mel-Spectrogram from waveform.
        
        Args:
            waveform (torch.Tensor): Audio waveform
            
        Returns:
            torch.Tensor: Mel-Spectrogram (1, 224, 224)
        """
        # Generate Mel-Spectrogram
        mel_spec = self.mel_spectrogram(waveform)
        
        # Convert to dB scale
        mel_spec_db = self.amplitude_to_db(mel_spec)
        
        # Resize to 224x224 (MobileNetV2 input size)
        # Current shape: (1, 224, time_steps)
        # We need to resize the time dimension to 224
        mel_spec_resized = torch.nn.functional.interpolate(
            mel_spec_db.unsqueeze(0),  # Add batch dimension
            size=(224, 224),
            mode='bilinear',
            align_corners=False
        ).squeeze(0)  # Remove batch dimension
        
        # Normalize to [0, 1]
        mel_spec_normalized = (mel_spec_resized - mel_spec_resized.min()) / (
            mel_spec_resized.max() - mel_spec_resized.min() + 1e-8
        )
        
        return mel_spec_normalized
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        """
        Get a single sample.
        
        Returns:
            tuple: (spectrogram, label)
                spectrogram: torch.Tensor of shape (1, 224, 224)
                label: torch.Tensor of shape (1,) with value 0 or 1
        """
        audio_filename, label = self.samples[idx]
        
        # Construct full path
        audio_path = os.path.join(self.data_dir, 'flac', audio_filename)
        
        # Check if file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load and preprocess audio
        waveform = self._load_audio(audio_path)
        
        # Generate spectrogram
        spectrogram = self._generate_spectrogram(waveform)
        
        # Convert label to tensor
        label_tensor = torch.tensor([label], dtype=torch.float32)
        
        return spectrogram, label_tensor


def get_dataloaders(data_root, protocol_root, batch_size=16, num_workers=4):
    """
    Create DataLoaders for training and validation.
    
    Args:
        data_root (str): Root directory containing ASVspoof2019_LA_train, dev, eval
        protocol_root (str): Root directory containing protocol files
        batch_size (int): Batch size for training
        num_workers (int): Number of worker processes for data loading
        
    Returns:
        tuple: (train_loader, dev_loader)
    """
    # Paths
    train_data_dir = os.path.join(data_root, 'LA', 'ASVspoof2019_LA_train')
    dev_data_dir = os.path.join(data_root, 'LA', 'ASVspoof2019_LA_dev')
    
    train_protocol = os.path.join(protocol_root, 'ASVspoof2019.LA.cm.train.trn.txt')
    dev_protocol = os.path.join(protocol_root, 'ASVspoof2019.LA.cm.dev.trl.txt')
    
    # Create datasets
    train_dataset = ASVspoofDataset(
        data_dir=train_data_dir,
        protocol_file=train_protocol,
        subset='train'
    )
    
    dev_dataset = ASVspoofDataset(
        data_dir=dev_data_dir,
        protocol_file=dev_protocol,
        subset='dev'
    )
    
    # Create dataloaders
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    dev_loader = torch.utils.data.DataLoader(
        dev_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, dev_loader


if __name__ == '__main__':
    # Test dataset loading
    print("Testing ASVspoofDataset...")
    
    # Example paths (adjust to your setup)
    data_root = 'data'
    protocol_root = os.path.join(data_root, 'ASVspoof2019_LA_cm_protocols')
    
    try:
        train_loader, dev_loader = get_dataloaders(data_root, protocol_root, batch_size=4, num_workers=0)
        
        print(f"Train dataset size: {len(train_loader.dataset)}")
        print(f"Dev dataset size: {len(dev_loader.dataset)}")
        
        # Test loading a batch
        for spectrograms, labels in train_loader:
            print(f"Batch spectrogram shape: {spectrograms.shape}")
            print(f"Batch labels shape: {labels.shape}")
            print(f"Sample labels: {labels[:5].squeeze()}")
            break
            
        print("Dataset test successful!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please download the ASVspoof 2019 LA dataset and place it in the 'data' directory.")

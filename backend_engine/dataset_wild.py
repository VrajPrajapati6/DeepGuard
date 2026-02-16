"""
In-the-Wild Dataset Loader for DeepGuard Fine-Tuning
Handles real-world audio with compression artifacts, background noise, and varying quality.
Compatible with MP3/AAC formats and applies same preprocessing as ASVspoof dataset.
"""

import os
import torch
import torchaudio
import torchaudio.transforms as T
from torch.utils.data import Dataset, DataLoader
import random
import numpy as np


class InTheWildDataset(Dataset):
    """
    Dataset loader for In-the-Wild deepfake audio.
    
    Expected directory structure:
        wild_data/
        ├── meta.csv        (CSV with columns: file, speaker, label)
        ├── 0.wav
        ├── 1.wav
        └── ...
    
    The meta.csv file contains:
    - file: filename (e.g., "0.wav")
    - speaker: speaker name
    - label: "bona-fide" (real) or "spoof" (fake)
    
    Applies same preprocessing as ASVspoof dataset with additional augmentation
    for robustness to real-world conditions.
    """
    
    def __init__(self, data_root, subset='train', target_sr=16000, 
                 duration=4.0, augment=True, augment_prob=0.2):
        """
        Initialize In-the-Wild dataset.
        
        Args:
            data_root: Root directory containing bona-fide and spoof folders
            subset: 'train' or 'val' (affects augmentation)
            target_sr: Target sample rate (16kHz to match ASVspoof)
            duration: Target duration in seconds (4.0 to match ASVspoof)
            augment: Whether to apply augmentation
            augment_prob: Probability of applying each augmentation (0.0-1.0)
        """
        self.data_root = data_root
        self.subset = subset
        self.target_sr = target_sr
        self.duration = duration
        self.target_length = int(target_sr * duration)
        self.augment = augment and (subset == 'train')
        self.augment_prob = augment_prob
        
        # Mel-Spectrogram parameters (same as ASVspoof dataset)
        self.n_fft = 2048
        self.hop_length = 512
        self.n_mels = 128
        
        # Load file paths and labels
        self.samples = self._load_samples()
        
        print(f"Loaded {len(self.samples)} samples from In-the-Wild {subset} set")
        print(f"  Real: {sum([1 for _, label in self.samples if label == 1])}")
        print(f"  Fake: {sum([1 for _, label in self.samples if label == 0])}")
    
    def _load_samples(self):
        """
        Load all audio files from meta.csv file.
        
        Returns:
            List of (file_path, label) tuples
        """
        import csv
        
        samples = []
        meta_file = os.path.join(self.data_root, 'meta.csv')
        
        if not os.path.exists(meta_file):
            raise ValueError(f"meta.csv not found in {self.data_root}")
        
        # Read CSV file
        with open(meta_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row['file']
                label_str = row['label']
                
                # Convert label: 'bona-fide' = 1 (real), 'spoof' = 0 (fake)
                label = 1 if label_str == 'bona-fide' else 0
                
                # Full path to audio file
                file_path = os.path.join(self.data_root, filename)
                
                # Check if file exists
                if os.path.exists(file_path):
                    samples.append((file_path, label))
                else:
                    print(f"Warning: File not found: {file_path}")
        
        if len(samples) == 0:
            raise ValueError(f"No audio files found in {self.data_root}")
        
        return samples
    
    def _load_audio(self, audio_path):
        """
        Load and preprocess audio file.
        Handles various formats including compressed audio (MP3, AAC).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            torch.Tensor: Preprocessed audio waveform
        """
        try:
            # Load audio with soundfile (handles MP3/AAC via ffmpeg backend)
            import soundfile as sf
            waveform_np, sr = sf.read(audio_path, dtype='float32')
            
            # Convert to torch tensor and add channel dimension
            waveform = torch.from_numpy(waveform_np).unsqueeze(0)  # (1, samples)
            
            # Convert to mono if stereo
            if len(waveform_np.shape) > 1 and waveform_np.shape[1] > 1:
                waveform = torch.from_numpy(waveform_np.mean(axis=1)).unsqueeze(0)
            
        except Exception as e:
            # Fallback to torchaudio for formats soundfile doesn't support
            print(f"Warning: soundfile failed for {audio_path}, trying torchaudio: {e}")
            try:
                waveform, sr = torchaudio.load(audio_path)
                # Convert to mono if stereo
                if waveform.shape[0] > 1:
                    waveform = torch.mean(waveform, dim=0, keepdim=True)
            except Exception as e2:
                raise RuntimeError(f"Failed to load {audio_path}: {e2}")
        
        # Resample if necessary
        if sr != self.target_sr:
            resampler = T.Resample(orig_freq=sr, new_freq=self.target_sr)
            waveform = resampler(waveform)
        
        # Pad or trim to target length
        if waveform.shape[1] < self.target_length:
            # Pad with zeros
            padding = self.target_length - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))
        elif waveform.shape[1] > self.target_length:
            # Trim to target length (random crop for training, center crop for val)
            if self.subset == 'train':
                start = random.randint(0, waveform.shape[1] - self.target_length)
            else:
                start = (waveform.shape[1] - self.target_length) // 2
            waveform = waveform[:, start:start + self.target_length]
        
        return waveform
    
    def _apply_augmentation(self, waveform):
        """
        Apply augmentation to simulate worse connection quality.
        
        Args:
            waveform: Input audio waveform
            
        Returns:
            Augmented waveform
        """
        if not self.augment:
            return waveform
        
        # Gaussian noise (simulate poor microphone quality)
        if random.random() < self.augment_prob:
            noise_level = random.uniform(0.001, 0.005)
            noise = torch.randn_like(waveform) * noise_level
            waveform = waveform + noise
        
        # Time masking (simulate packet loss in VoIP)
        if random.random() < self.augment_prob:
            mask_length = random.randint(800, 3200)  # 50-200ms at 16kHz
            mask_start = random.randint(0, waveform.shape[1] - mask_length)
            waveform[:, mask_start:mask_start + mask_length] *= 0.1  # Reduce to 10%
        
        # Volume variation (simulate AGC issues)
        if random.random() < self.augment_prob:
            volume_factor = random.uniform(0.7, 1.3)
            waveform = waveform * volume_factor
        
        return waveform
    
    def _generate_spectrogram(self, waveform):
        """
        Generate Mel-Spectrogram from waveform.
        Same preprocessing as ASVspoof dataset.
        
        Args:
            waveform: Input audio waveform (1, samples)
            
        Returns:
            torch.Tensor: Mel-Spectrogram (1, 224, 224)
        """
        # Create Mel-Spectrogram
        mel_spectrogram = T.MelSpectrogram(
            sample_rate=self.target_sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels
        )
        
        # Generate spectrogram
        mel_spec = mel_spectrogram(waveform)  # (1, n_mels, time)
        
        # Convert to dB scale
        mel_spec_db = T.AmplitudeToDB()(mel_spec)
        
        # Resize to 224x224 for MobileNetV2
        resize = torch.nn.functional.interpolate(
            mel_spec_db.unsqueeze(0),  # (1, 1, n_mels, time)
            size=(224, 224),
            mode='bilinear',
            align_corners=False
        )
        mel_spec_resized = resize.squeeze(0)  # (1, 224, 224)
        
        # Normalize to [0, 1]
        mel_spec_min = mel_spec_resized.min()
        mel_spec_max = mel_spec_resized.max()
        
        if mel_spec_max > mel_spec_min:
            mel_spec_normalized = (mel_spec_resized - mel_spec_min) / (mel_spec_max - mel_spec_min)
        else:
            mel_spec_normalized = torch.zeros_like(mel_spec_resized)
        
        return mel_spec_normalized
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        """
        Get a single sample.
        
        Returns:
            tuple: (spectrogram, label)
                - spectrogram: torch.Tensor of shape (1, 224, 224)
                - label: torch.Tensor of shape (1,) with value 0 or 1
        """
        audio_path, label = self.samples[idx]
        
        # Load audio
        waveform = self._load_audio(audio_path)
        
        # Apply augmentation
        waveform = self._apply_augmentation(waveform)
        
        # Generate spectrogram
        spectrogram = self._generate_spectrogram(waveform)
        
        # Convert label to tensor
        label_tensor = torch.tensor([label], dtype=torch.float32)
        
        return spectrogram, label_tensor


def get_wild_dataloaders(data_root, batch_size=16, num_workers=4, 
                         train_split=0.8, augment_prob=0.2):
    """
    Create train and validation dataloaders for In-the-Wild dataset.
    
    Args:
        data_root: Root directory containing bona-fide and spoof folders
        batch_size: Batch size for training
        num_workers: Number of data loading workers
        train_split: Fraction of data to use for training (rest for validation)
        augment_prob: Probability of applying each augmentation
        
    Returns:
        tuple: (train_loader, val_loader)
    """
    # Load all samples
    full_dataset = InTheWildDataset(
        data_root=data_root,
        subset='train',
        augment=True,
        augment_prob=augment_prob
    )
    
    # Split into train and validation
    total_size = len(full_dataset)
    train_size = int(total_size * train_split)
    val_size = total_size - train_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, 
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)  # Reproducible split
    )
    
    # Create validation dataset without augmentation
    val_dataset_no_aug = InTheWildDataset(
        data_root=data_root,
        subset='val',
        augment=False
    )
    
    # Use only the validation indices
    val_indices = val_dataset.indices
    val_dataset_no_aug.samples = [full_dataset.samples[i] for i in val_indices]
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset_no_aug,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader

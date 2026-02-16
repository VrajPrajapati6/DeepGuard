"""
DeepGuard Training Script
Trains MobileNetV2 on ASVspoof 2019 LA dataset for deepfake audio detection.
Optimized for Apple Silicon (MPS) with CPU fallback.
"""

import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.models as models
from tqdm import tqdm
import time
from dataset import get_dataloaders


class DeepGuardModel(nn.Module):
    """
    MobileNetV2-based binary classifier for deepfake detection.
    """
    
    def __init__(self, pretrained=True):
        super(DeepGuardModel, self).__init__()
        
        # Load pre-trained MobileNetV2
        self.mobilenet = models.mobilenet_v2(pretrained=pretrained)
        
        # Modify first convolutional layer to accept 1-channel input (grayscale spectrogram)
        # Original: Conv2d(3, 32, kernel_size=3, stride=2, padding=1)
        # We'll duplicate the spectrogram to 3 channels instead for simplicity
        # This preserves pre-trained weights
        
        # Modify classifier for binary classification
        # Original classifier outputs 1000 classes
        # We need 1 output (sigmoid activation for binary)
        in_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(in_features, 1)  # Single output for binary classification
        )
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 1, 224, 224)
            
        Returns:
            Output tensor of shape (batch_size, 1)
        """
        # Duplicate single channel to 3 channels for MobileNetV2
        x = x.repeat(1, 3, 1, 1)  # (batch_size, 3, 224, 224)
        
        # Forward through MobileNetV2
        return self.mobilenet(x)


def get_device():
    """
    Get the best available device (MPS for Apple Silicon, CUDA for NVIDIA, or CPU).
    """
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using Apple Silicon MPS acceleration")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA acceleration")
    else:
        device = torch.device("cpu")
        print("Using CPU (training will be slow)")
    
    return device


def train_epoch(model, train_loader, criterion, optimizer, device):
    """
    Train for one epoch.
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc="Training")
    
    for spectrograms, labels in pbar:
        # Move to device
        spectrograms = spectrograms.to(device)
        labels = labels.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(spectrograms)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item()
        
        # Calculate accuracy
        predictions = (torch.sigmoid(outputs) > 0.5).float()
        correct += (predictions == labels).sum().item()
        total += labels.size(0)
        
        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{100 * correct / total:.2f}%'
        })
    
    epoch_loss = running_loss / len(train_loader)
    epoch_acc = 100 * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, val_loader, criterion, device):
    """
    Validate the model with detailed metrics.
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    # Track per-class accuracy
    true_positives = 0  # Real detected as Real
    true_negatives = 0  # Fake detected as Fake
    false_positives = 0  # Fake detected as Real
    false_negatives = 0  # Real detected as Fake
    
    with torch.no_grad():
        pbar = tqdm(val_loader, desc="Validation")
        
        for spectrograms, labels in pbar:
            # Move to device
            spectrograms = spectrograms.to(device)
            labels = labels.to(device)
            
            # Forward pass
            outputs = model(spectrograms)
            loss = criterion(outputs, labels)
            
            # Statistics
            running_loss += loss.item()
            
            # Calculate accuracy
            predictions = (torch.sigmoid(outputs) > 0.5).float()
            
            # Update confusion matrix values
            true_positives += ((predictions == 1) & (labels == 1)).sum().item()
            true_negatives += ((predictions == 0) & (labels == 0)).sum().item()
            false_positives += ((predictions == 1) & (labels == 0)).sum().item()
            false_negatives += ((predictions == 0) & (labels == 1)).sum().item()
            
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
            
            # Update progress bar
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100 * correct / total:.2f}%'
            })
    
    epoch_loss = running_loss / len(val_loader)
    epoch_acc = 100 * correct / total
    
    # Print detailed metrics
    print(f"\n{'='*60}")
    print(f"Detailed Validation Metrics:")
    print(f"{'='*60}")
    print(f"  True Positives (Real → Real):  {true_positives:6d}")
    print(f"  True Negatives (Fake → Fake):  {true_negatives:6d}")
    print(f"  False Positives (Fake → Real): {false_positives:6d}")
    print(f"  False Negatives (Real → Fake): {false_negatives:6d}")
    print(f"{'-'*60}")
    
    # Calculate precision and recall
    if true_positives + false_negatives > 0:
        recall = true_positives / (true_positives + false_negatives)
        print(f"  Recall (Real):     {recall:.4f} ({recall*100:.2f}%)")
    
    if true_positives + false_positives > 0:
        precision = true_positives / (true_positives + false_positives)
        print(f"  Precision (Real):  {precision:.4f} ({precision*100:.2f}%)")
    
    if true_negatives + false_positives > 0:
        specificity = true_negatives / (true_negatives + false_positives)
        print(f"  Specificity (Fake): {specificity:.4f} ({specificity*100:.2f}%)")
    
    print(f"{'='*60}\n")
    
    return epoch_loss, epoch_acc


def main(args):
    """
    Main training function.
    """
    print("=" * 60)
    print("DeepGuard Training - Deepfake Audio Detection")
    print("=" * 60)
    
    # Set device
    device = get_device()
    
    # Create dataloaders
    print("\nLoading dataset...")
    data_root = args.data_dir
    protocol_root = os.path.join(data_root, 'LA', 'ASVspoof2019_LA_cm_protocols')
    
    train_loader, dev_loader = get_dataloaders(
        data_root=data_root,
        protocol_root=protocol_root,
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )
    
    print(f"Train samples: {len(train_loader.dataset)}")
    print(f"Validation samples: {len(dev_loader.dataset)}")
    
    # Verify no data leakage
    print("\nVerifying data integrity...")
    train_files = set([sample[0] for sample in train_loader.dataset.samples])
    dev_files = set([sample[0] for sample in dev_loader.dataset.samples])
    overlap = train_files.intersection(dev_files)
    
    if overlap:
        print(f"⚠️  WARNING: Found {len(overlap)} overlapping files between train and dev!")
        print(f"   First few overlaps: {list(overlap)[:5]}")
    else:
        print(f"✓ No overlap detected between train and dev sets")
    
    # Check label distribution
    train_labels = [sample[1] for sample in train_loader.dataset.samples]
    dev_labels = [sample[1] for sample in dev_loader.dataset.samples]
    
    train_real = sum(train_labels)
    train_fake = len(train_labels) - train_real
    dev_real = sum(dev_labels)
    dev_fake = len(dev_labels) - dev_real
    
    print(f"\nLabel Distribution:")
    print(f"  Train: {train_real} real ({train_real/len(train_labels)*100:.1f}%), {train_fake} fake ({train_fake/len(train_labels)*100:.1f}%)")
    print(f"  Dev:   {dev_real} real ({dev_real/len(dev_labels)*100:.1f}%), {dev_fake} fake ({dev_fake/len(dev_labels)*100:.1f}%)")
    
    # Create model
    print("\nInitializing model...")
    model = DeepGuardModel(pretrained=True)
    model = model.to(device)
    
    # Calculate class weights for imbalanced dataset
    # pos_weight = num_negative / num_positive (weight for positive class)
    pos_weight = torch.tensor([train_fake / train_real]).to(device)
    print(f"\nClass weight for real audio: {pos_weight.item():.2f}x")
    print(f"This compensates for the {train_fake/train_real:.1f}:1 imbalance\n")
    
    # Loss and optimizer with weighted loss
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3
    )
    
    # Training loop
    print("\nStarting training...")
    best_val_loss = float('inf')
    best_val_acc = 0.0
    patience_counter = 0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        print("-" * 60)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        
        # Validate
        val_loss, val_acc = validate(model, dev_loader, criterion, device)
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = val_acc
            patience_counter = 0
            
            # Save model
            model_path = os.path.join(args.model_dir, 'deepguard_model.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_acc': val_acc,
            }, model_path)
            
            print(f"✓ Model saved to {model_path}")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= args.patience:
            print(f"\nEarly stopping triggered after {epoch + 1} epochs")
            break
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print(f"Best Validation Loss: {best_val_loss:.4f}")
    print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train DeepGuard deepfake detection model')
    
    parser.add_argument('--data-dir', type=str, default='data',
                        help='Path to ASVspoof dataset directory')
    parser.add_argument('--model-dir', type=str, default='models',
                        help='Directory to save trained models')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=30,
                        help='Number of training epochs')
    parser.add_argument('--learning-rate', type=float, default=0.0001,
                        help='Learning rate')
    parser.add_argument('--num-workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--patience', type=int, default=5,
                        help='Early stopping patience')
    
    args = parser.parse_args()
    
    # Create model directory if it doesn't exist
    os.makedirs(args.model_dir, exist_ok=True)
    
    main(args)

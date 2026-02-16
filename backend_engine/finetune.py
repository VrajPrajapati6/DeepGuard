"""
DeepGuard Fine-Tuning Script
Fine-tunes the pre-trained model on In-the-Wild dataset for real-world robustness.
Uses transfer learning with layer freezing to preserve core features.
"""

import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import time
from dataset_wild import get_wild_dataloaders
from train import DeepGuardModel, get_device, validate


def freeze_layers(model, freeze_ratio=0.5):
    """
    Freeze the first N% of MobileNetV2 layers to preserve learned features.
    
    Args:
        model: DeepGuardModel instance
        freeze_ratio: Fraction of layers to freeze (0.0-1.0)
    """
    # Get all feature layers (excluding classifier)
    feature_layers = list(model.mobilenet.features.children())
    num_layers = len(feature_layers)
    num_freeze = int(num_layers * freeze_ratio)
    
    print(f"\nFreezing {num_freeze}/{num_layers} feature extraction layers ({freeze_ratio*100:.0f}%)")
    
    # Freeze early layers
    for i, layer in enumerate(feature_layers[:num_freeze]):
        for param in layer.parameters():
            param.requires_grad = False
        print(f"  ✓ Frozen layer {i+1}")
    
    # Keep later layers trainable
    for i, layer in enumerate(feature_layers[num_freeze:], start=num_freeze):
        for param in layer.parameters():
            param.requires_grad = True
        print(f"  ✓ Trainable layer {i+1}")
    
    # Always keep classifier trainable
    for param in model.mobilenet.classifier.parameters():
        param.requires_grad = True
    print(f"  ✓ Classifier fully trainable")
    
    # Count trainable parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nParameter Summary:")
    print(f"  Total: {total_params:,}")
    print(f"  Trainable: {trainable_params:,} ({trainable_params/total_params*100:.1f}%)")
    print(f"  Frozen: {total_params - trainable_params:,} ({(total_params-trainable_params)/total_params*100:.1f}%)")


def train_epoch(model, train_loader, criterion, optimizer, device):
    """
    Train for one epoch.
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc="Fine-tuning")
    
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


def main(args):
    """
    Main fine-tuning function.
    """
    print("=" * 60)
    print("DeepGuard Fine-Tuning - In-the-Wild Dataset")
    print("=" * 60)
    
    # Set device
    device = get_device()
    
    # Load pre-trained model
    print(f"\nLoading pre-trained model from {args.pretrained_model}...")
    
    if not os.path.exists(args.pretrained_model):
        raise FileNotFoundError(f"Pre-trained model not found: {args.pretrained_model}")
    
    # Create model
    model = DeepGuardModel(pretrained=False)  # Don't load ImageNet weights
    
    # Load trained weights
    checkpoint = torch.load(args.pretrained_model, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    
    print(f"✓ Loaded model from epoch {checkpoint['epoch']}")
    print(f"  Validation Loss: {checkpoint['val_loss']:.4f}")
    print(f"  Validation Accuracy: {checkpoint['val_acc']:.2f}%")
    
    # Move to device
    model = model.to(device)
    
    # Freeze layers
    freeze_layers(model, freeze_ratio=args.freeze_ratio)
    
    # Load In-the-Wild dataset
    print(f"\nLoading In-the-Wild dataset from {args.data_dir}...")
    train_loader, val_loader = get_wild_dataloaders(
        data_root=args.data_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        train_split=args.train_split,
        augment_prob=args.augment_prob
    )
    
    print(f"Train samples: {len(train_loader.dataset)}")
    print(f"Validation samples: {len(val_loader.dataset)}")
    
    # Calculate class weights if needed
    if args.use_class_weights:
        # Count labels in training set
        train_labels = []
        for _, labels in train_loader:
            train_labels.extend(labels.squeeze().tolist())
        
        train_real = sum(train_labels)
        train_fake = len(train_labels) - train_real
        
        pos_weight = torch.tensor([train_fake / train_real]).to(device)
        print(f"\nClass weight for real audio: {pos_weight.item():.2f}x")
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    else:
        criterion = nn.BCEWithLogitsLoss()
    
    # Optimizer with lower learning rate for fine-tuning
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),  # Only trainable params
        lr=args.learning_rate
    )
    
    print(f"\nFine-tuning with learning rate: {args.learning_rate}")
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=2
    )
    
    # Fine-tuning loop
    print("\nStarting fine-tuning...")
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
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        print(f"Learning Rate: {current_lr:.6f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = val_acc
            patience_counter = 0
            
            # Save model
            model_path = os.path.join(args.model_dir, args.output_model)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'val_acc': val_acc,
                'base_model': args.pretrained_model,
                'freeze_ratio': args.freeze_ratio,
            }, model_path)
            
            print(f"✓ Model saved to {model_path}")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= args.patience:
            print(f"\nEarly stopping triggered after {epoch + 1} epochs")
            break
    
    print("\n" + "=" * 60)
    print("Fine-Tuning Complete!")
    print(f"Best Validation Loss: {best_val_loss:.4f}")
    print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
    print("=" * 60)
    
    print(f"\nFine-tuned model saved as: {args.output_model}")
    print("Next steps:")
    print("  1. Export to ONNX: python export_v2_onnx.py")
    print("  2. Test on Windows with AMD GPU")
    print("  3. Compare v1 vs v2 performance")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fine-tune DeepGuard on In-the-Wild dataset')
    
    parser.add_argument('--pretrained-model', type=str, default='models/deepguard_model.pth',
                        help='Path to pre-trained model checkpoint')
    parser.add_argument('--data-dir', type=str, default='data/release_in_the_wild',
                        help='Path to In-the-Wild dataset directory')
    parser.add_argument('--model-dir', type=str, default='models',
                        help='Directory to save fine-tuned model')
    parser.add_argument('--output-model', type=str, default='deepguard_v2_robust.pth',
                        help='Output model filename')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Batch size for fine-tuning')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of fine-tuning epochs')
    parser.add_argument('--learning-rate', type=float, default=1e-5,
                        help='Learning rate (lower than initial training)')
    parser.add_argument('--num-workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--patience', type=int, default=3,
                        help='Early stopping patience')
    parser.add_argument('--freeze-ratio', type=float, default=0.5,
                        help='Fraction of layers to freeze (0.0-1.0)')
    parser.add_argument('--train-split', type=float, default=0.8,
                        help='Fraction of data for training (rest for validation)')
    parser.add_argument('--augment-prob', type=float, default=0.2,
                        help='Probability of applying each augmentation')
    parser.add_argument('--use-class-weights', action='store_true',
                        help='Use class weights for imbalanced data')
    
    args = parser.parse_args()
    
    # Create model directory if it doesn't exist
    os.makedirs(args.model_dir, exist_ok=True)
    
    main(args)

"""
ONNX Export for DeepGuard v2 (Fine-tuned Model)
Exports the fine-tuned robust model to ONNX format for Windows deployment.
"""

import os
import argparse
import torch
import onnx
import onnxruntime as ort
import numpy as np
from train import DeepGuardModel


def export_to_onnx(model_path, output_path, opset_version=12):
    """
    Export fine-tuned PyTorch model to ONNX format.
    
    Args:
        model_path: Path to fine-tuned model checkpoint
        output_path: Path to save ONNX model
        opset_version: ONNX opset version (12 for DirectML compatibility)
    """
    print("=" * 60)
    print("DeepGuard v2 ONNX Export")
    print("=" * 60)
    
    # Load model
    print(f"\nLoading fine-tuned model from {model_path}...")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Create model
    model = DeepGuardModel(pretrained=False)
    
    # Load weights
    checkpoint = torch.load(model_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    print(f"✓ Loaded model from epoch {checkpoint['epoch']}")
    print(f"  Validation Loss: {checkpoint['val_loss']:.4f}")
    print(f"  Validation Accuracy: {checkpoint['val_acc']:.2f}%")
    
    if 'base_model' in checkpoint:
        print(f"  Base Model: {checkpoint['base_model']}")
    if 'freeze_ratio' in checkpoint:
        print(f"  Freeze Ratio: {checkpoint['freeze_ratio']*100:.0f}%")
    
    # Create dummy input (batch_size=1, channels=1, height=224, width=224)
    dummy_input = torch.randn(1, 1, 224, 224)
    
    print(f"\nExporting to ONNX...")
    print(f"  Input shape: {tuple(dummy_input.shape)}")
    print(f"  Opset version: {opset_version}")
    
    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    print(f"✓ Model exported to {output_path}")
    
    # Validate ONNX model
    print(f"\nValidating ONNX model...")
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    print("✓ ONNX model is valid")
    
    # Test inference with ONNX Runtime
    print(f"\nTesting ONNX Runtime inference...")
    
    # Create session
    session = ort.InferenceSession(output_path)
    
    # Get input/output names
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    
    print(f"  Input: {input_name} {session.get_inputs()[0].shape}")
    print(f"  Output: {output_name} {session.get_outputs()[0].shape}")
    
    # Run inference
    test_input = np.random.randn(1, 1, 224, 224).astype(np.float32)
    onnx_output = session.run([output_name], {input_name: test_input})[0]
    
    # Run PyTorch inference for comparison
    with torch.no_grad():
        pytorch_output = model(torch.from_numpy(test_input)).numpy()
    
    # Compare outputs
    max_diff = np.abs(onnx_output - pytorch_output).max()
    print(f"  Max difference between PyTorch and ONNX: {max_diff:.6f}")
    
    if max_diff < 1e-5:
        print("  ✓ ONNX model matches PyTorch model")
    else:
        print(f"  ⚠ Warning: Difference is larger than expected ({max_diff:.6f})")
    
    # Get model size
    model_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nModel size: {model_size_mb:.2f} MB")
    
    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    
    print(f"\nONNX model saved as: {output_path}")
    print("\nNext steps:")
    print("  1. Transfer to Windows machine")
    print("  2. Update inference_amd.py to use new model")
    print("  3. Test with real-world audio (Zoom recordings, etc.)")
    print("  4. Compare v1 vs v2 performance")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export DeepGuard v2 to ONNX')
    
    parser.add_argument('--model-path', type=str, default='models/deepguard_v2_robust.pth',
                        help='Path to fine-tuned model checkpoint')
    parser.add_argument('--output-path', type=str, default='models/deepguard_amd_v2.onnx',
                        help='Path to save ONNX model')
    parser.add_argument('--opset-version', type=int, default=12,
                        help='ONNX opset version (12 for DirectML)')
    
    args = parser.parse_args()
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    
    export_to_onnx(args.model_path, args.output_path, args.opset_version)

"""
ONNX Export Script
Converts trained PyTorch model to ONNX format for Windows deployment.
"""

import os
import torch
import torch.onnx
import argparse
from train import DeepGuardModel


def export_to_onnx(model_path, output_path, opset_version=12):
    """
    Export PyTorch model to ONNX format.
    
    Args:
        model_path (str): Path to trained .pth model
        output_path (str): Path to save .onnx model
        opset_version (int): ONNX opset version (12 for DirectML compatibility)
    """
    print("=" * 60)
    print("DeepGuard ONNX Export")
    print("=" * 60)
    
    # Load trained model
    print(f"\nLoading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location='cpu')
    
    model = DeepGuardModel(pretrained=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    print(f"Model loaded successfully!")
    print(f"  - Epoch: {checkpoint['epoch']}")
    print(f"  - Validation Loss: {checkpoint['val_loss']:.4f}")
    print(f"  - Validation Accuracy: {checkpoint['val_acc']:.2f}%")
    
    # Create dummy input (batch_size=1, channels=1, height=224, width=224)
    dummy_input = torch.randn(1, 1, 224, 224)
    
    # Export to ONNX
    print(f"\nExporting to ONNX (opset version {opset_version})...")
    
    torch.onnx.export(
        model,                          # Model to export
        dummy_input,                    # Dummy input
        output_path,                    # Output path
        export_params=True,             # Store trained parameters
        opset_version=opset_version,    # ONNX version
        do_constant_folding=True,       # Optimize constant folding
        input_names=['input'],          # Input tensor name
        output_names=['output'],        # Output tensor name
        dynamic_axes={
            'input': {0: 'batch_size'},     # Variable batch size
            'output': {0: 'batch_size'}
        }
    )
    
    print(f"✓ Model exported to {output_path}")
    
    # Validate ONNX model
    print("\nValidating ONNX model...")
    try:
        import onnx
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        print("✓ ONNX model is valid!")
        
        # Print model info
        print("\nModel Information:")
        print(f"  - IR Version: {onnx_model.ir_version}")
        print(f"  - Producer: {onnx_model.producer_name}")
        print(f"  - Opset Version: {onnx_model.opset_import[0].version}")
        
        # Print input/output info
        print("\nInput/Output Information:")
        for input_tensor in onnx_model.graph.input:
            print(f"  Input: {input_tensor.name}")
            shape = [dim.dim_value if dim.dim_value > 0 else 'dynamic' 
                     for dim in input_tensor.type.tensor_type.shape.dim]
            print(f"    Shape: {shape}")
        
        for output_tensor in onnx_model.graph.output:
            print(f"  Output: {output_tensor.name}")
            shape = [dim.dim_value if dim.dim_value > 0 else 'dynamic' 
                     for dim in output_tensor.type.tensor_type.shape.dim]
            print(f"    Shape: {shape}")
        
    except ImportError:
        print("Warning: onnx package not found. Skipping validation.")
        print("Install with: pip install onnx")
    except Exception as e:
        print(f"Warning: ONNX validation failed: {e}")
    
    # Test inference
    print("\nTesting ONNX inference...")
    try:
        import onnxruntime as ort
        
        # Create inference session
        session = ort.InferenceSession(output_path)
        
        # Run inference
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        
        dummy_input_np = dummy_input.numpy()
        result = session.run([output_name], {input_name: dummy_input_np})
        
        print(f"✓ ONNX inference successful!")
        print(f"  Output shape: {result[0].shape}")
        print(f"  Sample output: {result[0][0][0]:.4f}")
        
    except ImportError:
        print("Warning: onnxruntime not found. Skipping inference test.")
        print("Install with: pip install onnxruntime")
    except Exception as e:
        print(f"Warning: ONNX inference test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Transfer the .onnx file to your Windows machine")
    print("2. Install onnxruntime-directml on Windows:")
    print("   pip install onnxruntime-directml")
    print("3. Run inference_amd.py for real-time detection")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export DeepGuard model to ONNX')
    
    parser.add_argument('--model-path', type=str, default='models/deepguard_model.pth',
                        help='Path to trained PyTorch model')
    parser.add_argument('--output-path', type=str, default='models/deepguard_amd.onnx',
                        help='Path to save ONNX model')
    parser.add_argument('--opset-version', type=int, default=12,
                        help='ONNX opset version (12 for DirectML compatibility)')
    
    args = parser.parse_args()
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        print(f"Error: Model file not found at {args.model_path}")
        print("Please train the model first using train.py")
        exit(1)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    
    # Export
    export_to_onnx(args.model_path, args.output_path, args.opset_version)

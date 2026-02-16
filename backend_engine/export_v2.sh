#!/bin/bash
# DeepGuard v2 ONNX Export Script
# Exports the fine-tuned model to ONNX format for Windows deployment

cd "$(dirname "$0")"
source venv/bin/activate

echo "============================================================"
echo "DeepGuard v2 ONNX Export"
echo "============================================================"
echo ""

# Check if fine-tuned model exists
if [ ! -f "models/deepguard_v2_robust.pth" ]; then
    echo "❌ Error: Fine-tuned model not found!"
    echo "   Please fine-tune the model first:"
    echo "   ./finetune_model.sh"
    exit 1
fi

echo "✓ Fine-tuned model found"
echo ""

# Export to ONNX
echo "Exporting to ONNX format..."
echo ""

python3 export_v2_onnx.py \
  --model-path models/deepguard_v2_robust.pth \
  --output-path models/deepguard_amd_v2.onnx \
  --opset-version 12

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Export complete!"
    echo "============================================================"
    echo ""
    echo "ONNX model saved: models/deepguard_amd_v2.onnx"
    echo ""
    echo "Next steps:"
    echo "  1. Transfer deepguard_amd_v2.onnx to Windows machine"
    echo "  2. Update inference_amd.py to use new model"
    echo "  3. Test with real-world audio (Zoom calls, etc.)"
else
    echo ""
    echo "❌ Export failed!"
    exit 1
fi

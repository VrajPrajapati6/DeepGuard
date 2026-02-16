#!/bin/bash
# DeepGuard v2 Fine-Tuning Script
# Fine-tunes the pre-trained model on In-the-Wild dataset

cd "$(dirname "$0")"
source venv/bin/activate

echo "============================================================"
echo "DeepGuard v2 Fine-Tuning Pipeline"
echo "============================================================"
echo ""

# Check if pre-trained model exists
if [ ! -f "models/deepguard_model.pth" ]; then
    echo "❌ Error: Pre-trained model not found!"
    echo "   Please train the base model first:"
    echo "   ./train_model.sh"
    exit 1
fi

# Check if wild dataset exists
if [ ! -f "data/release_in_the_wild/meta.csv" ]; then
    echo "❌ Error: In-the-Wild dataset not found!"
    echo "   Expected file: data/release_in_the_wild/meta.csv"
    echo "   Dataset should contain:"
    echo "   - meta.csv (with file, speaker, label columns)"
    echo "   - Audio files (0.wav, 1.wav, etc.)"
    exit 1
fi

echo "✓ Pre-trained model found"
echo "✓ In-the-Wild dataset found"
echo ""

# Fine-tune the model
echo "Starting fine-tuning (this will take 30-60 minutes)..."
echo ""

python3 finetune.py \
  --pretrained-model models/deepguard_model.pth \
  --data-dir data/release_in_the_wild \
  --output-model deepguard_v2_robust.pth \
  --epochs 10 \
  --batch-size 16 \
  --learning-rate 1e-5 \
  --freeze-ratio 0.5 \
  --num-workers 4 \
  --augment-prob 0.2 \
  --use-class-weights

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Fine-tuning complete!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Export to ONNX: ./export_v2.sh"
    echo "  2. Test on Windows with AMD GPU"
    echo "  3. Compare v1 vs v2 performance"
else
    echo ""
    echo "❌ Fine-tuning failed!"
    exit 1
fi

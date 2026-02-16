#!/bin/bash
# Quick test script for DeepGuard v2 model

cd "$(dirname "$0")"
source venv/bin/activate

echo "============================================================"
echo "DeepGuard v2 Model Testing"
echo "============================================================"
echo ""

# Check if model exists
if [ ! -f "models/deepguard_v2_robust.pth" ]; then
    echo "❌ Error: Fine-tuned model not found!"
    echo "   Please run ./finetune_model.sh first"
    exit 1
fi

echo "Testing on 10 random samples from In-the-Wild dataset..."
echo ""

python3 test_model.py \
  --model-path models/deepguard_v2_robust.pth \
  --data-dir data/release_in_the_wild \
  --test-dataset \
  --num-samples 10

echo ""
echo "Test complete!"
echo ""
echo "To test on a custom audio file:"
echo "  python3 test_model.py --audio-file /path/to/your/audio.wav"

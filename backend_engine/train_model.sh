#!/bin/bash
# DeepGuard Training Script
# Run this to train the model with proper class imbalance handling

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting DeepGuard training with weighted loss..."
echo "This will take approximately 2-4 hours for 30 epochs"
echo ""

# Train with recommended parameters
python3 train.py \
  --epochs 30 \
  --batch-size 16 \
  --learning-rate 0.0001 \
  --num-workers 4 \
  --patience 7

echo ""
echo "Training complete! Check models/deepguard_model.pth"

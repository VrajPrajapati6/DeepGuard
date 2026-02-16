# DeepGuard 🛡️

**Real-time Deepfake Audio Detection System**

DeepGuard is an AI-powered desktop application that detects deepfake audio in real-time using deep learning. The system is trained on macOS (Apple Silicon) and deployed on Windows (AMD Ryzen) using ONNX for cross-platform compatibility.

---

## 🎯 Features

- **Real-time Detection**: Monitors audio input and provides instant deepfake detection
- **Trust Score**: Visual gauge showing 0-100% authenticity score
- **Color-Coded Alerts**: Green (authentic), Yellow (uncertain), Red (deepfake)
- **Audio Visualization**: Real-time waveform display
- **Alert History**: Tracks and displays detection events
- **Cross-Platform**: Train on Mac, deploy on Windows

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DeepGuard System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  macOS (Training)          →         Windows (Deployment)   │
│  ─────────────────                   ──────────────────     │
│  PyTorch + MPS                       ONNX + DirectML        │
│  MobileNetV2                         AMD GPU Acceleration   │
│  ASVspoof 2019 Dataset               Real-time Inference    │
│                                                              │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │   train.py   │ ──ONNX Export──→   │inference_amd │       │
│  └──────────────┘                    └──────────────┘       │
│                                             ↓                │
│                                      ┌──────────────┐       │
│                                      │ Flask-Socket │       │
│                                      └──────────────┘       │
│                                             ↓                │
│                                      ┌──────────────┐       │
│                                      │React+Electron│       │
│                                      └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend (AI Engine)**:

- PyTorch (training on macOS with MPS acceleration)
- ONNX Runtime with DirectML (inference on Windows with AMD GPU)
- Flask-SocketIO (real-time communication)
- Librosa (audio preprocessing)

**Frontend (Desktop App)**:

- React 18 (UI framework)
- Electron.js (desktop packaging)
- Socket.io-client (WebSocket communication)
- Styled Components (styling)

**Model**:

- MobileNetV2 (pre-trained on ImageNet, fine-tuned for deepfake detection)
- Input: Mel-Spectrograms (224x224)
- Output: Binary classification (Real vs. Fake)

---

## 📋 Prerequisites

### For Training (macOS)

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.8+
- ASVspoof 2019 LA dataset

### For Deployment (Windows)

- Windows 10/11
- AMD Ryzen processor with compatible GPU
- Python 3.8+
- Node.js 16+

---

## 🚀 Setup Instructions

### 1. Download Dataset

Download the ASVspoof 2019 LA dataset from the [official website](https://www.asvspoof.org/index2019.html).

Extract the dataset into `backend_engine/data/`:

```
backend_engine/data/
├── ASVspoof2019_LA_train/
├── ASVspoof2019_LA_dev/
├── ASVspoof2019_LA_eval/
└── ASVspoof2019_LA_cm_protocols/
```

### 2. Training on macOS

```bash
cd backend_engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install torch torchaudio torchvision librosa scipy scikit-learn tqdm onnx

# Train the model
python train.py --epochs 30 --batch-size 16

# Export to ONNX
python export_onnx.py
```

This will create `models/deepguard_model.pth` and `models/deepguard_amd.onnx`.

### 3. Deployment on Windows

**Transfer the ONNX model** from macOS to Windows:

- Copy `backend_engine/models/deepguard_amd.onnx` to your Windows machine

**Install Python dependencies**:

```bash
cd backend_engine

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install Windows-specific dependencies
pip install onnxruntime-directml pyaudio librosa scipy numpy flask flask-socketio flask-cors

# Test inference
python inference_amd.py
```

**Install and run the frontend**:

```bash
cd frontend_app

# Install dependencies
npm install

# Run in development mode
npm run electron-dev

# Or build for production
npm run build
npm run electron
```

---

## 🎮 Usage

### Starting the System

1. **Start the backend server** (Windows):

   ```bash
   cd backend_engine
   python app.py
   ```

2. **Launch the desktop app** (Windows):

   ```bash
   cd frontend_app
   npm run electron
   ```

3. **Click "Start Detection"** in the app to begin real-time monitoring

### Understanding the Trust Score

- **80-100% (Green)**: Audio is likely authentic
- **50-80% (Yellow)**: Uncertain, requires manual review
- **0-50% (Red)**: Deepfake detected

---

## 📁 Project Structure

```
DeepGuard/
├── backend_engine/           # Python AI Logic
│   ├── data/                 # ASVspoof 2019 dataset
│   ├── models/               # Trained models (.pth and .onnx)
│   ├── dataset.py            # Dataset loader
│   ├── train.py              # Training script
│   ├── export_onnx.py        # ONNX export
│   ├── inference_amd.py      # Windows inference engine
│   ├── app.py                # Flask-SocketIO server
│   └── requirements.txt      # Python dependencies
│
├── frontend_app/             # React + Electron
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── TrustGauge.js
│   │   │   ├── AudioVisualizer.js
│   │   │   └── AlertPanel.js
│   │   ├── App.js            # Main application
│   │   ├── index.js          # React entry point
│   │   └── index.css         # Global styles
│   ├── main.js               # Electron entry point
│   └── package.json          # Node dependencies
│
└── README.md                 # This file
```

---

## 🔧 Troubleshooting

### Training Issues

**MPS not available**:

- Ensure you're running on Apple Silicon (M1/M2/M3)
- Update to the latest macOS version
- The script will automatically fall back to CPU

**Out of memory**:

- Reduce batch size: `python train.py --batch-size 8`
- Close other applications

### Inference Issues

**DirectML not working**:

- Ensure you have the latest AMD GPU drivers
- Install onnxruntime-directml: `pip install onnxruntime-directml`
- Check available providers: The script will print active providers

**PyAudio installation fails**:

- Windows: Download the wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Install with: `pip install PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl`

**No audio input**:

- Check microphone permissions in Windows settings
- Ensure microphone is not being used by another application

### Frontend Issues

**Cannot connect to backend**:

- Ensure Flask server is running on port 5000
- Check firewall settings
- Verify BACKEND_URL in `src/App.js`

---

## 📊 Performance

- **Training Time**: ~2-4 hours on Apple M1 (30 epochs)
- **Inference Speed**: ~50ms per 4-second audio chunk (AMD GPU)
- **Model Size**: ~14MB (ONNX format)
- **Accuracy**: Depends on training data quality and epochs

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## 📄 License

MIT License - feel free to use this project for educational or commercial purposes.

---

## 🙏 Acknowledgments

- ASVspoof 2019 dataset creators
- PyTorch and ONNX communities
- React and Electron.js teams

---

## 📧 Support

For questions or issues, please open a GitHub issue or contact the development team.

---

**Built with ❤️ for a safer digital world**

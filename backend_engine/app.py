"""
Flask-SocketIO Backend Server
Provides real-time WebSocket communication between inference engine and frontend.
"""

import os
import sys
import time
import threading
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import inference engine (Windows only, will fail on Mac)
try:
    from inference_amd import DeepGuardInference, AudioCapture
    INFERENCE_AVAILABLE = True
except Exception as e:
    print(f"Warning: Inference engine not available: {e}")
    print("This is expected on macOS. Deploy on Windows for real-time inference.")
    INFERENCE_AVAILABLE = False


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global inference state
inference_engine = None
audio_capture = None
is_running = False


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'inference_available': INFERENCE_AVAILABLE,
        'is_running': is_running
    })


@app.route('/status')
def status():
    """Get current system status."""
    return jsonify({
        'inference_available': INFERENCE_AVAILABLE,
        'is_running': is_running,
        'model_loaded': inference_engine is not None
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('status', {
        'connected': True,
        'inference_available': INFERENCE_AVAILABLE
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


@socketio.on('start_inference')
def handle_start_inference():
    """Start real-time inference."""
    global inference_engine, audio_capture, is_running
    
    if not INFERENCE_AVAILABLE:
        emit('error', {'message': 'Inference engine not available on this platform'})
        return
    
    if is_running:
        emit('error', {'message': 'Inference already running'})
        return
    
    try:
        # Initialize inference engine
        model_path = os.path.join('models', 'deepguard_amd.onnx')
        
        if not os.path.exists(model_path):
            emit('error', {'message': f'Model not found at {model_path}'})
            return
        
        print('Initializing inference engine...')
        inference_engine = DeepGuardInference(model_path, use_gpu=True)
        
        # Callback for audio chunks
        def on_audio_chunk(chunk):
            """Process audio chunk and emit trust score."""
            trust_score = inference_engine.predict(chunk)
            
            # Emit to all connected clients
            socketio.emit('trust_score', {
                'score': float(trust_score),
                'timestamp': time.time()
            })
        
        # Start audio capture
        audio_capture = AudioCapture(callback=on_audio_chunk)
        audio_capture.start()
        
        is_running = True
        
        emit('inference_started', {'message': 'Real-time inference started'})
        print('✓ Inference started')
        
    except Exception as e:
        emit('error', {'message': f'Failed to start inference: {str(e)}'})
        print(f'Error starting inference: {e}')


@socketio.on('stop_inference')
def handle_stop_inference():
    """Stop real-time inference."""
    global audio_capture, is_running
    
    if not is_running:
        emit('error', {'message': 'Inference not running'})
        return
    
    try:
        if audio_capture:
            audio_capture.stop()
            audio_capture = None
        
        is_running = False
        
        emit('inference_stopped', {'message': 'Inference stopped'})
        print('✓ Inference stopped')
        
    except Exception as e:
        emit('error', {'message': f'Failed to stop inference: {str(e)}'})
        print(f'Error stopping inference: {e}')


def main():
    """Run Flask-SocketIO server."""
    print("=" * 60)
    print("DeepGuard Backend Server")
    print("=" * 60)
    print(f"Inference Available: {INFERENCE_AVAILABLE}")
    print("\nStarting server on http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()

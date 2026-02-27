"""
Flask-SocketIO Backend Server - Demo Mode
Provides real-time WebSocket communication with simulated trust scores.
This demo mode works on macOS without requiring PyAudio or inference engine.
"""

import os
import time
import threading
import random
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,  # Disable verbose logging
    engineio_logger=False  # Disable engine.io logging
)

# Global state
is_running = False
demo_thread = None


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'mode': 'demo',
        'inference_available': False,
        'is_running': is_running
    })


@app.route('/status')
def status():
    """Get current system status."""
    return jsonify({
        'mode': 'demo',
        'inference_available': False,
        'is_running': is_running,
        'model_loaded': False
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('✓ Client connected')
    emit('status', {
        'connected': True,
        'mode': 'demo',
        'inference_available': False
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('✗ Client disconnected')


def demo_inference_loop():
    """Simulate real-time inference with random trust scores."""
    global is_running
    
    print('🎬 Starting demo inference loop...')
    
    # Simulate different scenarios
    scenarios = [
        # Scenario 1: Mostly authentic (80-95%)
        {'duration': 10, 'min': 80, 'max': 95, 'name': 'Authentic Audio'},
        # Scenario 2: Uncertain (45-65%)
        {'duration': 8, 'min': 45, 'max': 65, 'name': 'Uncertain Audio'},
        # Scenario 3: Deepfake detected (10-40%)
        {'duration': 6, 'min': 10, 'max': 40, 'name': 'Deepfake Detected'},
        # Scenario 4: Mixed signals (20-90%)
        {'duration': 12, 'min': 20, 'max': 90, 'name': 'Mixed Signals'},
    ]
    
    scenario_index = 0
    scenario_start = time.time()
    current_scenario = scenarios[scenario_index]
    
    print(f'📊 Scenario: {current_scenario["name"]}')
    
    while is_running:
        # Check if we should switch scenarios
        if time.time() - scenario_start > current_scenario['duration']:
            scenario_index = (scenario_index + 1) % len(scenarios)
            current_scenario = scenarios[scenario_index]
            scenario_start = time.time()
            print(f'📊 Scenario: {current_scenario["name"]}')
        
        # Generate random trust score within scenario range
        trust_score = random.uniform(current_scenario['min'], current_scenario['max'])
        
        # Add some noise for realism
        trust_score += random.gauss(0, 2)
        trust_score = max(0, min(100, trust_score))  # Clamp to 0-100
        
        # Emit to all connected clients
        socketio.emit('trust_score', {
            'score': float(trust_score),
            'timestamp': time.time(),
            'mode': 'demo'
        })
        
        # Color-coded console output
        if trust_score >= 80:
            status = "✓ AUTHENTIC"
            color = "\033[92m"  # Green
        elif trust_score >= 50:
            status = "⚠ UNCERTAIN"
            color = "\033[93m"  # Yellow
        else:
            status = "✗ DEEPFAKE"
            color = "\033[91m"  # Red
        
        reset = "\033[0m"
        print(f"{color}Trust Score: {trust_score:.1f}% - {status}{reset}")
        
        # Wait before next update (simulate real-time processing)
        time.sleep(0.5)  # 2 updates per second
    
    print('🛑 Demo inference loop stopped')


@socketio.on('start_inference')
def handle_start_inference(*args):
    """Start demo inference."""
    global is_running, demo_thread
    
    if is_running:
        emit('error', {'message': 'Demo inference already running'})
        return
    
    print('▶️  Starting demo inference...')
    is_running = True
    
    # Start demo thread
    demo_thread = threading.Thread(target=demo_inference_loop, daemon=True)
    demo_thread.start()
    
    emit('inference_started', {
        'message': 'Demo inference started (simulated data)',
        'mode': 'demo'
    })
    print('✓ Demo inference started')


@socketio.on('stop_inference')
def handle_stop_inference(*args):
    """Stop demo inference."""
    global is_running
    
    if not is_running:
        emit('error', {'message': 'Demo inference not running'})
        return
    
    print('⏸️  Stopping demo inference...')
    is_running = False
    
    emit('inference_stopped', {
        'message': 'Demo inference stopped',
        'mode': 'demo'
    })
    print('✓ Demo inference stopped')


def main():
    """Run Flask-SocketIO server in demo mode."""
    print("=" * 60)
    print("🎭 DeepGuard Backend Server - DEMO MODE")
    print("=" * 60)
    print("Mode: Demo (Simulated Trust Scores)")
    print("Platform: macOS")
    print("Note: Real inference requires Windows + AMD GPU")
    print("")
    print("Starting server on http://localhost:5001")
    print("=" * 60)
    print("")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)


if __name__ == '__main__':
    main()

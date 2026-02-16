/**
 * DeepGuard Main Application
 * Real-time deepfake audio detection dashboard
 */

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import io from 'socket.io-client';
import TrustGauge from './components/TrustGauge';
import AudioVisualizer from './components/AudioVisualizer';
import AlertPanel from './components/AlertPanel';

const BACKEND_URL = 'http://localhost:5000';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
  color: #ffffff;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  padding: 2rem;
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  color: #a0aec0;
  font-weight: 300;
`;

const Dashboard = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
`;

const ControlPanel = styled(Card)`
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
`;

const Button = styled.button`
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  ${props => props.primary ? `
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
  ` : `
    background: rgba(255, 255, 255, 0.1);
    color: white;
    
    &:hover {
      background: rgba(255, 255, 255, 0.15);
    }
  `}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #a0aec0;
`;

const StatusDot = styled.div`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: ${props => props.connected ? '#48bb78' : '#f56565'};
  box-shadow: 0 0 10px ${props => props.connected ? '#48bb78' : '#f56565'};
`;

function App() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [inferenceRunning, setInferenceRunning] = useState(false);
  const [trustScore, setTrustScore] = useState(50);
  const [alerts, setAlerts] = useState([]);

  // Connect to backend
  useEffect(() => {
    const newSocket = io(BACKEND_URL);
    
    newSocket.on('connect', () => {
      console.log('Connected to backend');
      setConnected(true);
    });
    
    newSocket.on('disconnect', () => {
      console.log('Disconnected from backend');
      setConnected(false);
      setInferenceRunning(false);
    });
    
    newSocket.on('status', (data) => {
      console.log('Status:', data);
    });
    
    newSocket.on('trust_score', (data) => {
      setTrustScore(data.score);
      
      // Add alert if deepfake detected
      if (data.score < 50) {
        const alert = {
          id: Date.now(),
          timestamp: new Date(data.timestamp * 1000),
          score: data.score,
          message: 'Deepfake detected!'
        };
        setAlerts(prev => [alert, ...prev].slice(0, 10)); // Keep last 10 alerts
      }
    });
    
    newSocket.on('inference_started', (data) => {
      console.log('Inference started:', data);
      setInferenceRunning(true);
    });
    
    newSocket.on('inference_stopped', (data) => {
      console.log('Inference stopped:', data);
      setInferenceRunning(false);
    });
    
    newSocket.on('error', (data) => {
      console.error('Error:', data.message);
      alert(`Error: ${data.message}`);
    });
    
    setSocket(newSocket);
    
    return () => newSocket.close();
  }, []);

  const handleStartInference = () => {
    if (socket && connected) {
      socket.emit('start_inference');
    }
  };

  const handleStopInference = () => {
    if (socket && connected) {
      socket.emit('stop_inference');
    }
  };

  const handleClearAlerts = () => {
    setAlerts([]);
  };

  return (
    <AppContainer>
      <Header>
        <Title>🛡️ DeepGuard</Title>
        <Subtitle>Real-time Deepfake Audio Detection</Subtitle>
      </Header>

      <Dashboard>
        <ControlPanel>
          <StatusIndicator>
            <StatusDot connected={connected} />
            {connected ? 'Connected' : 'Disconnected'}
          </StatusIndicator>
          
          <Button 
            primary 
            onClick={handleStartInference}
            disabled={!connected || inferenceRunning}
          >
            Start Detection
          </Button>
          
          <Button 
            onClick={handleStopInference}
            disabled={!connected || !inferenceRunning}
          >
            Stop Detection
          </Button>
        </ControlPanel>

        <Card>
          <TrustGauge score={trustScore} />
        </Card>

        <Card>
          <AudioVisualizer isActive={inferenceRunning} />
        </Card>

        <Card style={{ gridColumn: '1 / -1' }}>
          <AlertPanel alerts={alerts} onClear={handleClearAlerts} />
        </Card>
      </Dashboard>
    </AppContainer>
  );
}

export default App;

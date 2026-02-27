/**
 * DeepGuard Main Application
 * Premium real-time deepfake audio detection dashboard
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { useWebSocket } from './hooks/useWebSocket';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import ConnectionStatus from './components/ConnectionStatus';
import StatisticsPanel from './components/StatisticsPanel';
import TrustGauge from './components/TrustGauge';
import AudioVisualizer from './components/AudioVisualizer';
import AlertPanel from './components/AlertPanel';

const BACKEND_URL = 'http://localhost:5001';

const AppContainer = styled.div`
  min-height: 100vh;
  background: var(--gradient-background);
  color: var(--color-text-primary);
  font-family: var(--font-family-primary);
  padding: var(--space-6);
  
  @media (max-width: 768px) {
    padding: var(--space-4);
  }
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: var(--space-8);
  animation: fadeIn var(--duration-slow) var(--ease-out);
`;

const TitleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
`;

const Logo = styled.div`
  font-size: var(--font-size-5xl);
  filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.5));
`;

const Title = styled.h1`
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-extrabold);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: var(--letter-spacing-tight);
  
  @media (max-width: 768px) {
    font-size: var(--font-size-4xl);
  }
`;

const Subtitle = styled.p`
  font-size: var(--font-size-lg);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-normal);
  margin: 0;
  letter-spacing: var(--letter-spacing-wide);
`;

const Dashboard = styled.div`
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
`;

const ControlBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-bg-card);
  backdrop-filter: blur(var(--blur-lg));
  border-radius: var(--radius-2xl);
  border: 1px solid var(--color-border-subtle);
  box-shadow: var(--shadow-xl);
  flex-wrap: wrap;
`;

const Controls = styled.div`
  display: flex;
  gap: var(--space-3);
  align-items: center;
`;

const Button = styled.button`
  padding: var(--space-3) var(--space-6);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  border: none;
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  position: relative;
  overflow: hidden;
  
  ${props => props.$primary ? `
    background: var(--gradient-primary);
    color: var(--color-text-primary);
    box-shadow: var(--shadow-md);
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: var(--shadow-glow-primary);
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
    }
  ` : `
    background: var(--color-bg-card);
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border-subtle);
    
    &:hover:not(:disabled) {
      background: var(--color-bg-card-hover);
      border-color: var(--color-border-medium);
    }
  `}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }
`;

const KeyboardHint = styled.span`
  display: inline-block;
  margin-left: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-normal);
  opacity: 0.7;
`;

const StatsSection = styled.div`
  animation: slideInUp var(--duration-slow) var(--ease-out);
`;

const GridSection = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--space-6);
  animation: slideInUp var(--duration-slow) var(--ease-out) 0.1s backwards;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background: var(--color-bg-card);
  backdrop-filter: blur(var(--blur-lg));
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  border: 1px solid var(--color-border-subtle);
  box-shadow: var(--shadow-xl);
  transition: all var(--duration-normal) var(--ease-out);
  
  &:hover {
    border-color: var(--color-border-medium);
    box-shadow: var(--shadow-2xl);
  }
`;

const FullWidthCard = styled(Card)`
  animation: slideInUp var(--duration-slow) var(--ease-out) 0.2s backwards;
`;

function App() {
  const [inferenceRunning, setInferenceRunning] = useState(false);
  const [trustScore, setTrustScore] = useState(50);
  const [alerts, setAlerts] = useState([]);
  const [sessionStart, setSessionStart] = useState(Date.now());
  const [uptime, setUptime] = useState(0);
  const [detectionCount, setDetectionCount] = useState(0);
  const [scoreHistory, setScoreHistory] = useState([]);

  // WebSocket connection with auto-reconnect
  const { connected, reconnecting, reconnectAttempt, emit, on, off, reconnect } = useWebSocket(BACKEND_URL);

  // Calculate statistics
  const averageTrustScore = useMemo(() => {
    if (scoreHistory.length === 0) return 50;
    return scoreHistory.reduce((sum, score) => sum + score, 0) / scoreHistory.length;
  }, [scoreHistory]);

  const detectionRate = useMemo(() => {
    if (uptime === 0) return 0;
    return (detectionCount / uptime) * 60; // per minute
  }, [detectionCount, uptime]);

  // Update uptime
  useEffect(() => {
    if (!inferenceRunning) return;
    
    const interval = setInterval(() => {
      setUptime(Math.floor((Date.now() - sessionStart) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [inferenceRunning, sessionStart]);

  // Stable handler references — defined with useCallback so the same function
  // object is passed to both on() and off(), enabling precise deregistration.
  const handleTrustScore = useCallback((data) => {
    setTrustScore(data.score);
    setDetectionCount(prev => prev + 1);
    setScoreHistory(prev => [...prev, data.score].slice(-100));

    if (data.score < 50) {
      const newAlert = {
        id: Date.now(),
        timestamp: new Date(data.timestamp * 1000),
        score: data.score,
        message: data.score < 30 ? 'Critical: Deepfake detected!' : 'Warning: Low trust score'
      };
      setAlerts(prev => [newAlert, ...prev].slice(0, 50));
    }
  }, []);

  const handleInferenceStarted = useCallback(() => {
    console.log('Inference started');
    setInferenceRunning(true);
    setSessionStart(Date.now());
    setUptime(0);
    setDetectionCount(0);
    setScoreHistory([]);
  }, []);

  const handleInferenceStopped = useCallback(() => {
    console.log('Inference stopped');
    setInferenceRunning(false);
  }, []);

  const handleError = useCallback((data) => {
    console.error('Error:', data.message);
    alert(`Error: ${data.message}`);
  }, []);

  // Register WebSocket event handlers ONCE on mount.
  // Empty dependency array is intentional — handlers are stable useCallback refs
  // and on/off are also stable. Re-running this effect on every render was the
  // second driver of the infinite reconnect loop.
  useEffect(() => {
    on('trust_score', handleTrustScore);
    on('inference_started', handleInferenceStarted);
    on('inference_stopped', handleInferenceStopped);
    on('error', handleError);

    return () => {
      off('trust_score', handleTrustScore);
      off('inference_started', handleInferenceStarted);
      off('inference_stopped', handleInferenceStopped);
      off('error', handleError);
    };
  }, []); // run once — handlers are stable refs, socket is managed inside useWebSocket

  // Control functions
  const handleStartInference = useCallback(() => {
    if (connected && !inferenceRunning) {
      emit('start_inference');
    }
  }, [connected, inferenceRunning, emit]);

  const handleStopInference = useCallback(() => {
    if (connected && inferenceRunning) {
      emit('stop_inference');
    }
  }, [connected, inferenceRunning, emit]);

  const handleClearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  const toggleInference = useCallback(() => {
    if (inferenceRunning) {
      handleStopInference();
    } else {
      handleStartInference();
    }
  }, [inferenceRunning, handleStartInference, handleStopInference]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    ' ': toggleInference,
    'c': handleClearAlerts,
    'r': reconnect
  }, connected);

  return (
    <AppContainer>
      <Header>
        <TitleContainer>
          <Logo>🛡️</Logo>
          <Title>DeepGuard</Title>
        </TitleContainer>
        <Subtitle>Real-time Deepfake Audio Detection</Subtitle>
      </Header>

      <Dashboard>
        <ControlBar>
          <ConnectionStatus
            connected={connected}
            reconnecting={reconnecting}
            reconnectAttempt={reconnectAttempt}
            onReconnect={reconnect}
          />
          
          <Controls>
            <Button
              $primary
              onClick={handleStartInference}
              disabled={!connected || inferenceRunning}
            >
              Start Detection
              <KeyboardHint>Space</KeyboardHint>
            </Button>
            
            <Button
              onClick={handleStopInference}
              disabled={!connected || !inferenceRunning}
            >
              Stop Detection
              <KeyboardHint>Space</KeyboardHint>
            </Button>
          </Controls>
        </ControlBar>

        <StatsSection>
          <StatisticsPanel
            totalDetections={detectionCount}
            uptime={uptime}
            averageTrustScore={averageTrustScore}
            detectionRate={detectionRate}
            isRunning={inferenceRunning}
          />
        </StatsSection>

        <GridSection>
          <Card>
            <TrustGauge score={trustScore} />
          </Card>

          <Card>
            <AudioVisualizer 
              isActive={inferenceRunning} 
              trustScore={trustScore}
            />
          </Card>
        </GridSection>

        <FullWidthCard>
          <AlertPanel 
            alerts={alerts} 
            onClear={handleClearAlerts} 
          />
        </FullWidthCard>
      </Dashboard>
    </AppContainer>
  );
}

export default App;

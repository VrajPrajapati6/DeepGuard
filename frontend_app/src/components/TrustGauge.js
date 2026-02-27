/**
 * Enhanced Trust Gauge Component
 * Premium gauge with historical trend and smooth animations
 */

import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes, css } from 'styled-components';

const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
`;

const GaugeContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-6);
  height: 100%;
  justify-content: center;
`;

const Title = styled.h3`
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
`;

const GaugeWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const GaugeSVG = styled.svg`
  transform: rotate(-90deg);
  filter: drop-shadow(0 0 20px ${props => props.$glowColor});
  transition: filter var(--duration-normal) var(--ease-out);
`;

const ScoreDisplay = styled.div`
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
`;

const ScoreValue = styled.div`
  font-size: 5rem;
  font-weight: var(--font-weight-extrabold);
  background: ${props => props.$gradient};
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  ${props => props.$pulse && css`animation: ${pulse} 0.5s var(--ease-out);`}
  transition: all var(--duration-normal) var(--ease-spring);
`;

const ScoreLabel = styled.div`
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-widest);
  font-weight: var(--font-weight-medium);
`;

const ConfidenceBar = styled.div`
  width: 60px;
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-1);
`;

const ConfidenceFill = styled.div`
  height: 100%;
  width: ${props => props.$confidence}%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--duration-normal) var(--ease-out);
`;

const StatusBadge = styled.div`
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-xl);
  background: ${props => props.$background};
  border: 1px solid ${props => props.$borderColor};
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: ${props => props.$color};
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  box-shadow: 0 0 20px ${props => props.$glowColor};
  transition: all var(--duration-normal) var(--ease-out);
`;

const TrendLine = styled.div`
  width: 100%;
  max-width: 300px;
  height: 40px;
  position: relative;
  margin-top: var(--space-4);
`;

const TrendCanvas = styled.canvas`
  width: 100%;
  height: 100%;
  opacity: 0.6;
`;

const ThresholdMarker = styled.div`
  position: absolute;
  width: 2px;
  height: 100%;
  background: ${props => props.$color};
  opacity: 0.3;
  left: ${props => props.$position}%;
  top: 0;
  
  &::after {
    content: '${props => props.$label}';
    position: absolute;
    top: -20px;
    left: 50%;
    transform: translateX(-50%);
    font-size: var(--font-size-xs);
    color: ${props => props.$color};
    white-space: nowrap;
  }
`;

function TrustGauge({ score = 50 }) {
  const [displayScore, setDisplayScore] = useState(score);
  const [pulse, setPulse] = useState(false);
  const [history, setHistory] = useState([]);
  const canvasRef = useRef(null);
  const prevScoreRef = useRef(score);

  // Animate score changes
  useEffect(() => {
    const diff = Math.abs(score - displayScore);
    if (diff > 0.5) {
      const timer = setInterval(() => {
        setDisplayScore(prev => {
          const step = (score - prev) * 0.1;
          if (Math.abs(step) < 0.5) return score;
          return prev + step;
        });
      }, 16);
      return () => clearInterval(timer);
    }
  }, [score, displayScore]);

  // Trigger pulse on score change
  useEffect(() => {
    if (Math.abs(score - prevScoreRef.current) > 5) {
      setPulse(true);
      setTimeout(() => setPulse(false), 500);
    }
    prevScoreRef.current = score;
  }, [score]);

  // Update history
  useEffect(() => {
    setHistory(prev => {
      const newHistory = [...prev, score];
      return newHistory.slice(-60); // Keep last 60 points
    });
  }, [score]);

  // Draw trend line
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || history.length < 2) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth * 2;
    const height = canvas.height = canvas.offsetHeight * 2;

    ctx.clearRect(0, 0, width, height);

    const step = width / (history.length - 1);
    
    ctx.beginPath();
    ctx.strokeStyle = getColor(displayScore).primary;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    history.forEach((value, i) => {
      const x = i * step;
      const y = height - (value / 100) * height;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
  }, [history, displayScore]);

  const clampedScore = Math.max(0, Math.min(100, displayScore));

  // Gauge parameters
  const size = 320;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedScore / 100) * circumference;

  // Get colors and status based on score
  const getColor = (score) => {
    if (score >= 80) return { 
      primary: '#22c55e', 
      secondary: '#16a34a',
      gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
      status: '✓ AUTHENTIC',
      bg: 'rgba(34, 197, 94, 0.15)',
      border: 'rgba(34, 197, 94, 0.3)',
      glow: 'rgba(34, 197, 94, 0.4)'
    };
    if (score >= 50) return { 
      primary: '#f97316', 
      secondary: '#ea580c',
      gradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
      status: '⚠ UNCERTAIN',
      bg: 'rgba(249, 115, 22, 0.15)',
      border: 'rgba(249, 115, 22, 0.3)',
      glow: 'rgba(249, 115, 22, 0.4)'
    };
    return { 
      primary: '#ef4444', 
      secondary: '#dc2626',
      gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      status: '✗ DEEPFAKE',
      bg: 'rgba(239, 68, 68, 0.15)',
      border: 'rgba(239, 68, 68, 0.3)',
      glow: 'rgba(239, 68, 68, 0.4)'
    };
  };

  const colors = getColor(clampedScore);
  const confidence = Math.min(100, 60 + (Math.abs(clampedScore - 50) / 50) * 40);

  return (
    <GaugeContainer>
      <Title>Trust Score</Title>

      <GaugeWrapper>
        <GaugeSVG width={size} height={size} $glowColor={colors.glow}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            fill="none"
          />

          {/* Threshold markers */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(249, 115, 22, 0.2)"
            strokeWidth={2}
            fill="none"
            strokeDasharray={`${circumference * 0.5} ${circumference * 0.5}`}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(34, 197, 94, 0.2)"
            strokeWidth={2}
            fill="none"
            strokeDasharray={`${circumference * 0.8} ${circumference * 0.2}`}
          />

          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colors.primary}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), stroke 0.5s ease'
            }}
          />
        </GaugeSVG>

        <ScoreDisplay>
          <ScoreValue $gradient={colors.gradient} $pulse={pulse}>
            {Math.round(clampedScore)}
          </ScoreValue>
          <ScoreLabel>Score</ScoreLabel>
          <ConfidenceBar>
            <ConfidenceFill $confidence={confidence} />
          </ConfidenceBar>
        </ScoreDisplay>
      </GaugeWrapper>

      <StatusBadge 
        $background={colors.bg}
        $borderColor={colors.border}
        $color={colors.primary}
        $glowColor={colors.glow}
      >
        {colors.status}
      </StatusBadge>

      {history.length > 1 && (
        <TrendLine>
          <TrendCanvas ref={canvasRef} />
        </TrendLine>
      )}
    </GaugeContainer>
  );
}

export default TrustGauge;

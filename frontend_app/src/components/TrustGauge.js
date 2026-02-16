/**
 * Trust Gauge Component
 * Displays the trust score as a circular gauge with color-coded zones
 */

import React from 'react';
import styled from 'styled-components';

const GaugeContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
`;

const GaugeTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: #e2e8f0;
`;

const GaugeSVG = styled.svg`
  transform: rotate(-90deg);
  filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3));
`;

const ScoreDisplay = styled.div`
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const ScoreValue = styled.div`
  font-size: 4rem;
  font-weight: 700;
  background: ${props => props.gradient};
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
`;

const ScoreLabel = styled.div`
  font-size: 1rem;
  color: #a0aec0;
  margin-top: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 2px;
`;

const StatusText = styled.div`
  font-size: 1.2rem;
  font-weight: 600;
  margin-top: 2rem;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  background: ${props => props.background};
  color: ${props => props.color};
`;

const GaugeWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
`;

function TrustGauge({ score = 50 }) {
  // Clamp score between 0 and 100
  const clampedScore = Math.max(0, Math.min(100, score));
  
  // Gauge parameters
  const size = 280;
  const strokeWidth = 20;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedScore / 100) * circumference;
  
  // Color coding based on score
  let strokeColor, gradient, statusText, statusBg, statusColor;
  
  if (clampedScore >= 80) {
    strokeColor = '#48bb78'; // Green
    gradient = 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
    statusText = '✓ AUTHENTIC';
    statusBg = 'rgba(72, 187, 120, 0.2)';
    statusColor = '#48bb78';
  } else if (clampedScore >= 50) {
    strokeColor = '#ed8936'; // Orange
    gradient = 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)';
    statusText = '⚠ UNCERTAIN';
    statusBg = 'rgba(237, 137, 54, 0.2)';
    statusColor = '#ed8936';
  } else {
    strokeColor = '#f56565'; // Red
    gradient = 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
    statusText = '✗ DEEPFAKE DETECTED';
    statusBg = 'rgba(245, 101, 101, 0.2)';
    statusColor = '#f56565';
  }
  
  return (
    <GaugeContainer>
      <GaugeTitle>Trust Score</GaugeTitle>
      
      <GaugeWrapper>
        <GaugeSVG width={size} height={size}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth={strokeWidth}
            fill="none"
          />
          
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.5s ease, stroke 0.5s ease'
            }}
          />
        </GaugeSVG>
        
        <ScoreDisplay>
          <ScoreValue gradient={gradient}>
            {Math.round(clampedScore)}
          </ScoreValue>
          <ScoreLabel>Score</ScoreLabel>
        </ScoreDisplay>
      </GaugeWrapper>
      
      <StatusText background={statusBg} color={statusColor}>
        {statusText}
      </StatusText>
    </GaugeContainer>
  );
}

export default TrustGauge;

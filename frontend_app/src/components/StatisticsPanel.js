/**
 * Statistics Panel Component
 * Displays real-time session statistics
 */

import React, { useMemo } from 'react';
import styled from 'styled-components';

const PanelContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
`;

const StatCard = styled.div`
  background: var(--color-bg-card);
  backdrop-filter: blur(var(--blur-lg));
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--duration-normal) var(--ease-out);

  &:hover {
    background: var(--color-bg-card-hover);
    border-color: var(--color-border-medium);
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
  }
`;

const StatLabel = styled.div`
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  margin-bottom: var(--space-2);
`;

const StatValue = styled.div`
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  background: ${props => props.$gradient || 'var(--gradient-primary)'};
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
  transition: all var(--duration-normal) var(--ease-spring);
`;

const StatSubtext = styled.div`
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-2);
`;

const TrendIndicator = styled.span`
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: ${props => props.$positive ? 'var(--color-success-400)' : 'var(--color-danger-400)'};
  margin-left: var(--space-2);
`;

function StatisticsPanel({ 
  totalDetections = 0,
  uptime = 0,
  averageTrustScore = 50,
  detectionRate = 0,
  isRunning = false
}) {
  // Format uptime as HH:MM:SS
  const formattedUptime = useMemo(() => {
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = uptime % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }, [uptime]);

  // Determine trust score gradient
  const trustScoreGradient = useMemo(() => {
    if (averageTrustScore >= 80) return 'var(--gradient-success)';
    if (averageTrustScore >= 50) return 'var(--gradient-warning)';
    return 'var(--gradient-danger)';
  }, [averageTrustScore]);

  return (
    <PanelContainer>
      <StatCard>
        <StatLabel>Total Detections</StatLabel>
        <StatValue $gradient="var(--gradient-primary)">
          {totalDetections.toLocaleString()}
        </StatValue>
        <StatSubtext>
          {isRunning ? 'Active monitoring' : 'Monitoring paused'}
        </StatSubtext>
      </StatCard>

      <StatCard>
        <StatLabel>Session Uptime</StatLabel>
        <StatValue $gradient="var(--gradient-secondary)">
          {formattedUptime}
        </StatValue>
        <StatSubtext>
          {isRunning ? 'Running' : 'Stopped'}
        </StatSubtext>
      </StatCard>

      <StatCard>
        <StatLabel>Average Trust Score</StatLabel>
        <StatValue $gradient={trustScoreGradient}>
          {Math.round(averageTrustScore)}%
        </StatValue>
        <StatSubtext>
          {averageTrustScore >= 80 ? 'Excellent' : 
           averageTrustScore >= 50 ? 'Moderate' : 'Low confidence'}
        </StatSubtext>
      </StatCard>

      <StatCard>
        <StatLabel>Detection Rate</StatLabel>
        <StatValue $gradient="var(--gradient-primary)">
          {detectionRate.toFixed(1)}
        </StatValue>
        <StatSubtext>
          detections per minute
        </StatSubtext>
      </StatCard>
    </PanelContainer>
  );
}

export default StatisticsPanel;

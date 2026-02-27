/**
 * Enhanced Alert Panel Component
 * Premium alert system with filtering and export functionality
 */

import React, { useState, useMemo } from 'react';
import styled, { keyframes, css } from 'styled-components';

const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const PanelContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
`;

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
`;

const Title = styled.h3`
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
`;

const HeaderActions = styled.div`
  display: flex;
  gap: var(--space-2);
  align-items: center;
`;

const FilterButton = styled.button`
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: ${props => props.$active ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)'};
  background: ${props => props.$active ? 'var(--color-bg-card)' : 'transparent'};
  border: 1px solid ${props => props.$active ? 'var(--color-border-medium)' : 'var(--color-border-subtle)'};
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);

  &:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-card);
    border-color: var(--color-border-medium);
  }
`;

const ActionButton = styled.button`
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: ${props => props.$primary ? 'var(--gradient-primary)' : 'var(--color-bg-card)'};
  border: 1px solid ${props => props.$primary ? 'transparent' : 'var(--color-border-subtle)'};
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: ${props => props.$primary ? 'var(--shadow-glow-primary)' : 'var(--shadow-md)'};
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
  }
`;

const AlertList = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  max-height: 400px;
  overflow-y: auto;
  padding-right: var(--space-2);

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: var(--color-bg-tertiary);
    border-radius: var(--radius-md);
  }

  &::-webkit-scrollbar-thumb {
    background: var(--color-border-medium);
    border-radius: var(--radius-md);
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-strong);
  }
`;

const AlertItem = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  background: ${props => props.$severity === 'high' ? 
    'rgba(239, 68, 68, 0.1)' : 
    props.$severity === 'medium' ? 
    'rgba(249, 115, 22, 0.1)' : 
    'rgba(100, 116, 139, 0.1)'
  };
  border-left: 3px solid ${props => props.$severity === 'high' ? 
    'var(--color-danger-500)' : 
    props.$severity === 'medium' ? 
    'var(--color-warning-500)' : 
    'var(--color-text-muted)'
  };
  border-radius: var(--radius-lg);
  ${css`animation: ${slideIn} var(--duration-normal) var(--ease-out);`}
  transition: all var(--duration-fast) var(--ease-out);

  &:hover {
    background: ${props => props.$severity === 'high' ? 
      'rgba(239, 68, 68, 0.15)' : 
      props.$severity === 'medium' ? 
      'rgba(249, 115, 22, 0.15)' : 
      'rgba(100, 116, 139, 0.15)'
    };
    transform: translateX(4px);
  }
`;

const AlertIcon = styled.div`
  font-size: var(--font-size-2xl);
  flex-shrink: 0;
`;

const AlertContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
`;

const AlertMessage = styled.div`
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: ${props => props.$severity === 'high' ? 
    'var(--color-danger-400)' : 
    props.$severity === 'medium' ? 
    'var(--color-warning-400)' : 
    'var(--color-text-secondary)'
  };
`;

const AlertTime = styled.div`
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
`;

const AlertScore = styled.div`
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: ${props => props.$severity === 'high' ? 
    'var(--color-danger-400)' : 
    props.$severity === 'medium' ? 
    'var(--color-warning-400)' : 
    'var(--color-text-muted)'
  };
  flex-shrink: 0;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: var(--space-16) var(--space-8);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-base);
  
  svg {
    width: 64px;
    height: 64px;
    margin-bottom: var(--space-4);
    opacity: 0.3;
  }
`;

const FILTERS = {
  ALL: 'all',
  HIGH: 'high',
  MEDIUM: 'medium'
};

function AlertPanel({ alerts = [], onClear }) {
  const [filter, setFilter] = useState(FILTERS.ALL);

  const getSeverity = (score) => {
    if (score < 30) return 'high';
    if (score < 50) return 'medium';
    return 'low';
  };

  const filteredAlerts = useMemo(() => {
    if (filter === FILTERS.ALL) return alerts;
    return alerts.filter(alert => getSeverity(alert.score) === filter);
  }, [alerts, filter]);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const exportAlerts = () => {
    const data = JSON.stringify(alerts, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `deepguard-alerts-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getIcon = (severity) => {
    if (severity === 'high') return '🚨';
    if (severity === 'medium') return '⚠️';
    return 'ℹ️';
  };

  return (
    <PanelContainer>
      <PanelHeader>
        <Title>Detection Alerts</Title>
        <HeaderActions>
          <FilterButton 
            $active={filter === FILTERS.ALL}
            onClick={() => setFilter(FILTERS.ALL)}
          >
            All ({alerts.length})
          </FilterButton>
          <FilterButton 
            $active={filter === FILTERS.HIGH}
            onClick={() => setFilter(FILTERS.HIGH)}
          >
            Critical ({alerts.filter(a => getSeverity(a.score) === 'high').length})
          </FilterButton>
          <FilterButton 
            $active={filter === FILTERS.MEDIUM}
            onClick={() => setFilter(FILTERS.MEDIUM)}
          >
            Warning ({alerts.filter(a => getSeverity(a.score) === 'medium').length})
          </FilterButton>
          <ActionButton onClick={exportAlerts} disabled={alerts.length === 0}>
            Export
          </ActionButton>
          <ActionButton $primary onClick={onClear} disabled={alerts.length === 0}>
            Clear All
          </ActionButton>
        </HeaderActions>
      </PanelHeader>

      {filteredAlerts.length === 0 ? (
        <EmptyState>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            {filter === FILTERS.ALL ? 
              'No alerts yet. Deepfake detections will appear here.' :
              `No ${filter} severity alerts.`
            }
          </div>
        </EmptyState>
      ) : (
        <AlertList>
          {filteredAlerts.map((alert) => {
            const severity = getSeverity(alert.score);
            return (
              <AlertItem key={alert.id} $severity={severity}>
                <AlertIcon>{getIcon(severity)}</AlertIcon>
                <AlertContent>
                  <AlertMessage $severity={severity}>
                    {alert.message}
                  </AlertMessage>
                  <AlertTime>{formatTime(alert.timestamp)}</AlertTime>
                </AlertContent>
                <AlertScore $severity={severity}>
                  {Math.round(alert.score)}%
                </AlertScore>
              </AlertItem>
            );
          })}
        </AlertList>
      )}
    </PanelContainer>
  );
}

export default AlertPanel;

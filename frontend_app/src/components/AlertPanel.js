/**
 * Alert Panel Component
 * Displays a history of deepfake detection alerts
 */

import React from 'react';
import styled from 'styled-components';

const PanelContainer = styled.div`
  display: flex;
  flex-direction: column;
  padding: 2rem;
`;

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const PanelTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
`;

const ClearButton = styled.button`
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.1);
  color: #a0aec0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #e2e8f0;
  }
  
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
`;

const AlertList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
  
  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const AlertItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(245, 101, 101, 0.1);
  border-left: 3px solid #f56565;
  border-radius: 8px;
  animation: slideIn 0.3s ease;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
`;

const AlertIcon = styled.div`
  font-size: 1.5rem;
`;

const AlertContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const AlertMessage = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: #f56565;
`;

const AlertTime = styled.div`
  font-size: 0.85rem;
  color: #a0aec0;
`;

const AlertScore = styled.div`
  font-size: 1.2rem;
  font-weight: 700;
  color: #f56565;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 1rem;
  color: #a0aec0;
  font-size: 1rem;
`;

function AlertPanel({ alerts = [], onClear }) {
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  return (
    <PanelContainer>
      <PanelHeader>
        <PanelTitle>Detection Alerts</PanelTitle>
        <ClearButton onClick={onClear} disabled={alerts.length === 0}>
          Clear All
        </ClearButton>
      </PanelHeader>
      
      {alerts.length === 0 ? (
        <EmptyState>
          No alerts yet. Deepfake detections will appear here.
        </EmptyState>
      ) : (
        <AlertList>
          {alerts.map((alert) => (
            <AlertItem key={alert.id}>
              <AlertIcon>⚠️</AlertIcon>
              <AlertContent>
                <AlertMessage>{alert.message}</AlertMessage>
                <AlertTime>{formatTime(alert.timestamp)}</AlertTime>
              </AlertContent>
              <AlertScore>{Math.round(alert.score)}%</AlertScore>
            </AlertItem>
          ))}
        </AlertList>
      )}
    </PanelContainer>
  );
}

export default AlertPanel;

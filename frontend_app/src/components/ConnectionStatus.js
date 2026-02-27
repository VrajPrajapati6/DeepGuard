/**
 * Connection Status Component
 * Premium connection indicator with retry functionality
 */

import React from 'react';
import styled, { keyframes, css } from 'styled-components';

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
`;

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const Container = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-card);
  backdrop-filter: blur(var(--blur-lg));
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--duration-normal) var(--ease-out);

  &:hover {
    background: var(--color-bg-card-hover);
    border-color: var(--color-border-medium);
  }
`;

const StatusDot = styled.div`
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  position: relative;
  
  ${props => {
    if (props.$connected) {
      return css`
        background: var(--color-success-500);
        box-shadow: 0 0 12px var(--color-success-500);
        animation: ${pulse} 2s var(--ease-in-out) infinite;
      `;
    } else if (props.$reconnecting) {
      return css`
        background: var(--color-warning-500);
        box-shadow: 0 0 12px var(--color-warning-500);
        animation: ${pulse} 1s var(--ease-in-out) infinite;
      `;
    } else {
      return css`
        background: var(--color-danger-500);
        box-shadow: 0 0 12px var(--color-danger-500);
      `;
    }
  }}
`;

const StatusText = styled.div`
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: ${props => 
    props.$connected ? 'var(--color-success-400)' :
    props.$reconnecting ? 'var(--color-warning-400)' :
    'var(--color-danger-400)'
  };
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
`;

const ReconnectButton = styled.button`
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow-primary);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const Spinner = styled.div`
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border-subtle);
  border-top-color: var(--color-warning-500);
  border-radius: var(--radius-full);
  ${css`animation: ${spin} 0.8s linear infinite;`}
`;

const AttemptCount = styled.span`
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-left: var(--space-2);
`;

function ConnectionStatus({ connected, reconnecting, reconnectAttempt, onReconnect }) {
  const getStatusText = () => {
    if (connected) return 'Connected';
    if (reconnecting) return 'Reconnecting';
    return 'Disconnected';
  };

  return (
    <Container>
      <StatusDot $connected={connected} $reconnecting={reconnecting} />
      <StatusText $connected={connected} $reconnecting={reconnecting}>
        {getStatusText()}
      </StatusText>
      
      {reconnecting && <Spinner />}
      
      {reconnecting && reconnectAttempt > 0 && (
        <AttemptCount>Attempt {reconnectAttempt}</AttemptCount>
      )}
      
      {!connected && !reconnecting && (
        <ReconnectButton onClick={onReconnect}>
          Retry Connection
        </ReconnectButton>
      )}
    </Container>
  );
}

export default ConnectionStatus;

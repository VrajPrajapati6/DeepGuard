/**
 * Audio Visualizer Component
 * Displays a visual representation of audio activity
 */

import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';

const VisualizerContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
`;

const VisualizerTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  color: #e2e8f0;
`;

const Canvas = styled.canvas`
  width: 100%;
  height: 200px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
`;

const StatusIndicator = styled.div`
  margin-top: 1.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  background: ${props => props.isActive ? 'rgba(72, 187, 120, 0.2)' : 'rgba(160, 174, 192, 0.2)'};
  color: ${props => props.isActive ? '#48bb78' : '#a0aec0'};
`;

function AudioVisualizer({ isActive = false }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const barsRef = useRef([]);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth * 2; // Retina display
    const height = canvas.height = canvas.offsetHeight * 2;
    
    const barCount = 64;
    const barWidth = width / barCount;
    
    // Initialize bars with random heights
    if (barsRef.current.length === 0) {
      barsRef.current = Array(barCount).fill(0).map(() => Math.random() * 0.3);
    }
    
    const draw = () => {
      // Clear canvas
      ctx.clearRect(0, 0, width, height);
      
      // Update bars
      barsRef.current = barsRef.current.map((bar, i) => {
        if (isActive) {
          // Simulate audio activity with random fluctuations
          const target = Math.random() * 0.8 + 0.2;
          return bar + (target - bar) * 0.1;
        } else {
          // Decay to zero when inactive
          return bar * 0.95;
        }
      });
      
      // Draw bars
      barsRef.current.forEach((bar, i) => {
        const x = i * barWidth;
        const barHeight = bar * height;
        const y = (height - barHeight) / 2;
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        gradient.addColorStop(1, 'rgba(118, 75, 162, 0.8)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
      });
      
      animationRef.current = requestAnimationFrame(draw);
    };
    
    draw();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive]);
  
  return (
    <VisualizerContainer>
      <VisualizerTitle>Audio Activity</VisualizerTitle>
      <Canvas ref={canvasRef} />
      <StatusIndicator isActive={isActive}>
        {isActive ? '🎤 Monitoring Audio' : '⏸ Inactive'}
      </StatusIndicator>
    </VisualizerContainer>
  );
}

export default AudioVisualizer;

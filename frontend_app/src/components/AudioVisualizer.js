/**
 * Enhanced Audio Visualizer Component
 * Premium visualizer with multiple modes and particle effects
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import styled from 'styled-components';
import { random } from '../utils/animations';

const VisualizerContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  height: 100%;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h3`
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
`;

const ModeSelector = styled.div`
  display: flex;
  gap: var(--space-2);
  background: var(--color-bg-tertiary);
  padding: var(--space-1);
  border-radius: var(--radius-lg);
`;

const ModeButton = styled.button`
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: ${props => props.$active ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)'};
  background: ${props => props.$active ? 'var(--color-bg-card)' : 'transparent'};
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);

  &:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-card);
  }
`;

const CanvasContainer = styled.div`
  position: relative;
  flex: 1;
  min-height: 250px;
  border-radius: var(--radius-xl);
  background: rgba(0, 0, 0, 0.3);
  overflow: hidden;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
`;

const Canvas = styled.canvas`
  width: 100%;
  height: 100%;
  display: block;
`;

const StatusBadge = styled.div`
  position: absolute;
  bottom: var(--space-4);
  left: var(--space-4);
  padding: var(--space-2) var(--space-4);
  background: ${props => props.$isActive ? 
    'rgba(34, 197, 94, 0.2)' : 
    'rgba(100, 116, 139, 0.2)'
  };
  backdrop-filter: blur(var(--blur-md));
  border: 1px solid ${props => props.$isActive ? 
    'var(--color-success-500)' : 
    'var(--color-border-subtle)'
  };
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: ${props => props.$isActive ? 
    'var(--color-success-400)' : 
    'var(--color-text-tertiary)'
  };
  display: flex;
  align-items: center;
  gap: var(--space-2);
`;

const Dot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: ${props => props.$isActive ? 
    'var(--color-success-500)' : 
    'var(--color-text-muted)'
  };
  box-shadow: ${props => props.$isActive ? 
    '0 0 10px var(--color-success-500)' : 
    'none'
  };
`;

const MODES = {
  BARS: 'bars',
  WAVEFORM: 'waveform',
  CIRCULAR: 'circular'
};

// Particle class for visual effects
class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.vx = random(-1, 1);
    this.vy = random(-2, -0.5);
    this.life = 1;
    this.decay = random(0.01, 0.03);
    this.size = random(2, 4);
    this.color = color;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.life -= this.decay;
    return this.life > 0;
  }

  draw(ctx) {
    ctx.save();
    ctx.globalAlpha = this.life;
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function AudioVisualizer({ isActive = false, trustScore = 50 }) {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const barsRef = useRef([]);
  const particlesRef = useRef([]);
  const [mode, setMode] = useState(MODES.BARS);

  // Determine color based on trust score
  const getColor = useMemo(() => {
    if (trustScore >= 80) return { primary: '#22c55e', secondary: '#16a34a' };
    if (trustScore >= 50) return { primary: '#f97316', secondary: '#ea580c' };
    return { primary: '#ef4444', secondary: '#dc2626' };
  }, [trustScore]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const updateSize = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    updateSize();
    window.addEventListener('resize', updateSize);

    const barCount = 64;
    const width = canvas.width / (window.devicePixelRatio || 1);
    const height = canvas.height / (window.devicePixelRatio || 1);

    // Initialize bars
    if (barsRef.current.length === 0) {
      barsRef.current = Array(barCount).fill(0).map(() => random(0.1, 0.3));
    }

    const drawBars = () => {
      const barWidth = width / barCount;

      barsRef.current.forEach((bar, i) => {
        const x = i * barWidth;
        const barHeight = bar * height * 0.8;
        const y = (height - barHeight) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, getColor.primary);
        gradient.addColorStop(1, getColor.secondary);

        ctx.fillStyle = gradient;
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);

        // Add glow effect
        if (isActive && bar > 0.5) {
          ctx.shadowBlur = 15;
          ctx.shadowColor = getColor.primary;
          ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
          ctx.shadowBlur = 0;
        }
      });
    };

    const drawWaveform = () => {
      ctx.beginPath();
      ctx.strokeStyle = getColor.primary;
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      const step = width / barsRef.current.length;
      
      barsRef.current.forEach((bar, i) => {
        const x = i * step;
        const y = height / 2 + (bar - 0.5) * height * 0.6;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();

      // Add glow
      if (isActive) {
        ctx.shadowBlur = 20;
        ctx.shadowColor = getColor.primary;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
    };

    const drawCircular = () => {
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.3;

      barsRef.current.forEach((bar, i) => {
        const angle = (i / barsRef.current.length) * Math.PI * 2 - Math.PI / 2;
        const barLength = bar * radius;
        
        const x1 = centerX + Math.cos(angle) * radius;
        const y1 = centerY + Math.sin(angle) * radius;
        const x2 = centerX + Math.cos(angle) * (radius + barLength);
        const y2 = centerY + Math.sin(angle) * (radius + barLength);

        const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
        gradient.addColorStop(0, getColor.secondary);
        gradient.addColorStop(1, getColor.primary);

        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Update bars
      barsRef.current = barsRef.current.map((bar) => {
        if (isActive) {
          const target = random(0.2, 0.9);
          return bar + (target - bar) * 0.15;
        } else {
          return bar * 0.95;
        }
      });

      // Draw based on mode
      switch (mode) {
        case MODES.WAVEFORM:
          drawWaveform();
          break;
        case MODES.CIRCULAR:
          drawCircular();
          break;
        case MODES.BARS:
        default:
          drawBars();
          break;
      }

      // Add particles when active
      if (isActive && Math.random() < 0.3) {
        const x = random(0, width);
        const y = height / 2;
        particlesRef.current.push(new Particle(x, y, getColor.primary));
      }

      // Update and draw particles
      particlesRef.current = particlesRef.current.filter(particle => {
        const alive = particle.update();
        if (alive) particle.draw(ctx);
        return alive;
      });

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', updateSize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, mode, getColor]);

  return (
    <VisualizerContainer>
      <Header>
        <Title>Audio Activity</Title>
        <ModeSelector>
          <ModeButton 
            $active={mode === MODES.BARS}
            onClick={() => setMode(MODES.BARS)}
          >
            Bars
          </ModeButton>
          <ModeButton 
            $active={mode === MODES.WAVEFORM}
            onClick={() => setMode(MODES.WAVEFORM)}
          >
            Wave
          </ModeButton>
          <ModeButton 
            $active={mode === MODES.CIRCULAR}
            onClick={() => setMode(MODES.CIRCULAR)}
          >
            Circular
          </ModeButton>
        </ModeSelector>
      </Header>

      <CanvasContainer>
        <Canvas ref={canvasRef} />
        <StatusBadge $isActive={isActive}>
          <Dot $isActive={isActive} />
          {isActive ? 'Monitoring' : 'Inactive'}
        </StatusBadge>
      </CanvasContainer>
    </VisualizerContainer>
  );
}

export default AudioVisualizer;

/**
 * Animation Utilities
 * Reusable animation functions and helpers
 */

// Spring physics for smooth transitions
export function spring(value, target, velocity, options = {}) {
  const {
    stiffness = 170,
    damping = 26,
    mass = 1,
    precision = 0.01
  } = options;

  const force = -stiffness * (value - target);
  const dampingForce = -damping * velocity;
  const acceleration = (force + dampingForce) / mass;
  
  const newVelocity = velocity + acceleration * (1 / 60); // 60fps
  const newValue = value + newVelocity * (1 / 60);

  // Check if we're close enough to stop
  if (Math.abs(newValue - target) < precision && Math.abs(newVelocity) < precision) {
    return { value: target, velocity: 0, done: true };
  }

  return { value: newValue, velocity: newVelocity, done: false };
}

// Easing functions
export const easing = {
  linear: t => t,
  easeIn: t => t * t,
  easeOut: t => t * (2 - t),
  easeInOut: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  easeInCubic: t => t * t * t,
  easeOutCubic: t => (--t) * t * t + 1,
  easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  easeInQuart: t => t * t * t * t,
  easeOutQuart: t => 1 - (--t) * t * t * t,
  easeInOutQuart: t => t < 0.5 ? 8 * t * t * t * t : 1 - 8 * (--t) * t * t * t,
  easeInElastic: t => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0 ? 0 : t === 1 ? 1 : -Math.pow(2, 10 * t - 10) * Math.sin((t * 10 - 10.75) * c4);
  },
  easeOutElastic: t => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },
  easeInBounce: t => 1 - easing.easeOutBounce(1 - t),
  easeOutBounce: t => {
    const n1 = 7.5625;
    const d1 = 2.75;
    if (t < 1 / d1) {
      return n1 * t * t;
    } else if (t < 2 / d1) {
      return n1 * (t -= 1.5 / d1) * t + 0.75;
    } else if (t < 2.5 / d1) {
      return n1 * (t -= 2.25 / d1) * t + 0.9375;
    } else {
      return n1 * (t -= 2.625 / d1) * t + 0.984375;
    }
  }
};

// Interpolate between two values
export function lerp(start, end, t) {
  return start + (end - start) * t;
}

// Clamp value between min and max
export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

// Map value from one range to another
export function mapRange(value, inMin, inMax, outMin, outMax) {
  return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
}

// Stagger animation delays for list items
export function staggerDelay(index, baseDelay = 50, maxDelay = 500) {
  return Math.min(index * baseDelay, maxDelay);
}

// Generate random value in range
export function random(min, max) {
  return Math.random() * (max - min) + min;
}

// Smooth step function
export function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

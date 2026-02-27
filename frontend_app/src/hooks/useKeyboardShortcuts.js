/**
 * Custom Keyboard Shortcuts Hook
 * Manages keyboard shortcuts with conflict prevention
 */

import { useEffect, useCallback, useRef } from 'react';

export function useKeyboardShortcuts(shortcuts = {}, enabled = true) {
  const shortcutsRef = useRef(shortcuts);
  
  // Update shortcuts ref when they change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    // Don't trigger shortcuts when typing in inputs
    const target = event.target;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return;
    }

    const key = event.key.toLowerCase();
    const ctrl = event.ctrlKey || event.metaKey;
    const shift = event.shiftKey;
    const alt = event.altKey;

    // Build shortcut string
    let shortcutKey = '';
    if (ctrl) shortcutKey += 'ctrl+';
    if (shift) shortcutKey += 'shift+';
    if (alt) shortcutKey += 'alt+';
    shortcutKey += key;

    // Check if this shortcut is registered
    const handler = shortcutsRef.current[shortcutKey] || shortcutsRef.current[key];
    
    if (handler) {
      event.preventDefault();
      handler(event);
    }
  }, [enabled]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Hook for showing keyboard shortcuts help
export function useShortcutHelp() {
  const shortcuts = [
    { key: 'Space', description: 'Start/Stop detection' },
    { key: 'C', description: 'Clear alerts' },
    { key: 'S', description: 'Open settings' },
    { key: 'H', description: 'View history' },
    { key: '?', description: 'Show keyboard shortcuts' },
    { key: 'Esc', description: 'Close panels' }
  ];

  return shortcuts;
}

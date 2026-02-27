/**
 * Custom WebSocket Hook
 * Manages Socket.IO connection using the library's built-in reconnection logic.
 *
 * DESIGN: Handlers registered via on() are stored in a Map (listenersRef).
 * On every socket 'connect' event, all stored handlers are re-applied to the
 * socket. This means it doesn't matter whether on() is called before or after
 * the socket connects — handlers are always active.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import io from 'socket.io-client';

export function useWebSocket(url) {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const socketRef = useRef(null);
  // Map of event → handler. Persists across reconnects.
  const listenersRef = useRef(new Map());

  // Initialize connection ONCE on mount.
  useEffect(() => {
    const socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
      randomizationFactor: 0.5,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
      setReconnecting(false);
      setReconnectAttempt(0);

      // Re-apply all registered handlers after every (re)connect.
      // This ensures handlers registered via on() before or after connection
      // are always active on the live socket.
      listenersRef.current.forEach((handler, event) => {
        socket.off(event, handler);
        socket.on(event, handler);
      });
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnected(false);
      if (reason !== 'io server disconnect') {
        setReconnecting(true);
      }
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error.message);
      setConnected(false);
      setReconnecting(true);
    });

    socket.on('reconnect_attempt', (attempt) => {
      console.log(`Reconnect attempt #${attempt}`);
      setReconnectAttempt(attempt);
      setReconnecting(true);
    });

    socket.on('reconnect', () => {
      console.log('WebSocket reconnected');
      setConnected(true);
      setReconnecting(false);
      setReconnectAttempt(0);
    });

    socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed permanently');
      setReconnecting(false);
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [url]);

  // Emit an event to the server
  const emit = useCallback((event, data) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
      return true;
    }
    console.warn(`Cannot emit "${event}": socket not connected`);
    return false;
  }, []);

  // Register an event listener.
  // Stores the handler in listenersRef so it survives reconnects,
  // and immediately applies it to the socket if already connected.
  const on = useCallback((event, handler) => {
    listenersRef.current.set(event, handler);
    if (socketRef.current) {
      socketRef.current.off(event, handler);
      socketRef.current.on(event, handler);
    }
  }, []);

  // Unregister an event listener
  const off = useCallback((event, handler) => {
    listenersRef.current.delete(event);
    if (socketRef.current) {
      socketRef.current.off(event, handler);
    }
  }, []);

  // Manual reconnect
  const reconnect = useCallback(() => {
    if (!socketRef.current) return;
    socketRef.current.disconnect();
    socketRef.current.connect();
  }, []);

  return {
    socket: socketRef.current,
    connected,
    reconnecting,
    reconnectAttempt,
    emit,
    on,
    off,
    reconnect,
  };
}

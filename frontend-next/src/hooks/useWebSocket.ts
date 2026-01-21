import { useEffect, useState, useRef, useCallback } from 'react';

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

const URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws';

export function useWebSocket(url: string = URL) {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [history, setHistory] = useState<WebSocketMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>(undefined);

  const connect = useCallback(() => {
    try {
      setStatus('connecting');
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setStatus('connected');
        console.log('[WS] Connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const message = {
            ...data,
            timestamp: new Date().toISOString()
          };
          setLastMessage(message);
          setHistory(prev => [message, ...prev].slice(0, 100)); // Keep last 100 logs
        } catch (e) {
          console.error('[WS] Parse error', e);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        socketRef.current = null;
        // Reconnect after 3s
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (e) => {
        console.error('[WS] Error', e);
        setStatus('error');
      };

      socketRef.current = ws;
    } catch (e) {
      setStatus('error');
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return { status, lastMessage, history };
}

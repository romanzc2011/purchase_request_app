import { useEffect, useRef, useState } from "react";

export function useWebSockets(WEBSOCKET_URL: string, onMessage?: (e: MessageEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMsgRef = useRef(onMessage);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // ms

  // keep latest onMessage without re-creating the socket
  useEffect(() => { onMsgRef.current = onMessage; }, [onMessage]);

  useEffect(() => {
    let unmounted = false;

    const connect = () => {
      // prevent duplicates (StrictMode, re-renders, etc.)
      const s = wsRef.current;
      if (s && (s.readyState === WebSocket.OPEN || s.readyState === WebSocket.CONNECTING)) return;

      const ws = new WebSocket(WEBSOCKET_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("🔗 WebSocket connected to:", WEBSOCKET_URL);
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // heartbeat every 25s to keep proxies happy
        if (!pingRef.current) {
          pingRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ t: "ping" }));
            }
          }, 25000);
        }
      };

      ws.onmessage = (e) => {
        onMsgRef.current?.(e);
      };

      ws.onclose = (e) => {
        console.log("🔌 WebSocket disconnected, code:", e.code, "reason:", e.reason);
        setIsConnected(false);

        // clear heartbeat
        if (pingRef.current) {
          clearInterval(pingRef.current);
          pingRef.current = null;
        }

        // normal close (1000) or unmounted: don't reconnect
        if (unmounted || e.code === 1000) return;

        // backoff reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * 2 ** reconnectAttemptsRef.current;
          reconnectTimerRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        // let onclose handle reconnection
      };
    };

    connect();

    return () => {
      unmounted = true;

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (pingRef.current) {
        clearInterval(pingRef.current);
        pingRef.current = null;
      }
      // close the *actual* socket
      const s = wsRef.current;
      if (s && s.readyState === WebSocket.OPEN) s.close(1000, "unmount");
      wsRef.current = null;
    };
  }, [WEBSOCKET_URL]);

  return { socket: wsRef.current, isConnected };
}

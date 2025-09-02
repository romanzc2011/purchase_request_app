import { useEffect, useMemo, useRef, useState } from "react";
import { computeWSURL } from "../utils/sio_client";

export function useWebSockets(path = "/communicate", onMessage?: (e: MessageEvent)=>void) {
  const url = useMemo(() => computeWSURL(path), [path]);
  const wsRef = useRef<WebSocket | null>(null);
  const onMsgRef = useRef(onMessage);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => { onMsgRef.current = onMessage; }, [onMessage]);

  useEffect(() => {
    let unmounted = false;

    const connect = () => {
      const s = wsRef.current;
      if (s && (s.readyState === WebSocket.OPEN || s.readyState === WebSocket.CONNECTING)) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        attemptsRef.current = 0;
        if (!pingRef.current) {
          pingRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) ws.send('{"t":"ping"}');
          }, 25000);
        }
      };

      ws.onmessage = (e) => onMsgRef.current?.(e);

      ws.onclose = (e) => {
        setIsConnected(false);
        if (pingRef.current) { clearInterval(pingRef.current); pingRef.current = null; }
        if (unmounted || e.code === 1000) return;
        if (attemptsRef.current < 5) {
          const delay = 1000 * 2 ** attemptsRef.current++;
          retryRef.current = setTimeout(connect, delay);
        }
      };
    };

    connect();

    return () => {
      unmounted = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      if (pingRef.current) clearInterval(pingRef.current);
      const s = wsRef.current;
      if (s && s.readyState === WebSocket.OPEN) s.close(1000, "unmount");
      wsRef.current = null;
    };
  }, [url]);

  return { socket: wsRef.current, isConnected };
}

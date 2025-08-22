import { computeWSURL } from "../utils/ws";

let socket: WebSocket | null = null;
let openPromise: Promise<WebSocket> | null = null;
const listeners = new Set<(ev: MessageEvent) => void>();
const QUEUE: string[] = [];

function init() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        return;
    }

  socket = new WebSocket(computeWSURL()); 

  // Resolve when open; re-create if it drops
  openPromise = new Promise<WebSocket>((resolve) => {
    if (!socket) return;

    socket.onopen = () => {
      // Flush any queued messages
      for (const m of QUEUE) socket!.send(m);
      QUEUE.length = 0;
      resolve(socket!);
    };

    socket.onmessage = (event) => {
      for (const cb of listeners) cb(event);
    };

    socket.onclose = () => {
      // Optional: exponential backoff etc. For now, try a sixmple reconnect
      setTimeout(() => init(), 1000);
    };

    socket.onerror = () => {
      // Let onclose handle reconnect; apps usually just log here
    };
  });
}

export function connectSocket(): Promise<WebSocket> {
  init();
  return openPromise!;
}

export function sendJSON(payload: unknown) {
  const data = JSON.stringify(payload);
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(data);
  } else {
    // Not open yet — queue until onopen
    QUEUE.push(data);
    init();
  }
}

export function addMessageListener(cb: (ev: MessageEvent) => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function getReadyState(): number | null {
  return socket?.readyState ?? null;
}

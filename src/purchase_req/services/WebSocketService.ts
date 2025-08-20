import { computeWSURL } from "../utils/ws";

class WebSocketService {
    private socket: WebSocket | null = null;
    private listeners = new Map<string, Array<(d: any) => void>>();
    private isConnected = false;
    private queue: string[] = [];
    
    //-------------------------------------------------------------
    // CONNECT
    //-------------------------------------------------------------
    connect() {
      if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) return;
  
      this.socket = new WebSocket(computeWSURL("/communicate"));
  
      this.socket.onopen = () => {
        this.isConnected = true;
        for (const m of this.queue) this.socket!.send(m);
        this.queue.length = 0;
        this.notifyListeners({ event: "open" });
      };
  
      this.socket.onmessage = (evt) => {
        let payload: any = evt.data;
        try { if (typeof payload === "string") payload = JSON.parse(payload); } catch {}
        this.notifyListeners(payload);
      };
  
      this.socket.onclose = (e) => {
        this.isConnected = false;
        this.notifyListeners({ event: "close", code: e.code, reason: e.reason });
      };
  
      this.socket.onerror = (e) => this.notifyListeners({ event: "error", error: e });
    }
  
    //-------------------------------------------------------------
    // DISCONNECT
    //-------------------------------------------------------------
    disconnect() {
      this.socket?.close();
      this.socket = null;
      this.isConnected = false;
    }
  
    //-------------------------------------------------------------
    // SEND
    //-------------------------------------------------------------
    send(obj: any) {
      const msg = JSON.stringify(obj);
      if (this.socket && this.isConnected) this.socket.send(msg);
      else this.queue.push(msg);
    }
  
    //-------------------------------------------------------------
    // SUBSCRIBE
    //-------------------------------------------------------------
    subscribe(event: string, cb: (data: any) => void) {
      const arr = this.listeners.get(event) ?? [];
      arr.push(cb);
      this.listeners.set(event, arr);
      return () => {
        const list = this.listeners.get(event);
        if (!list) return;
        const i = list.indexOf(cb);
        if (i > -1) list.splice(i, 1);
        if (list.length === 0) this.listeners.delete(event);
      };
    }
  
    private notifyListeners(data: any) {
      const evt = data?.event ?? "message";
      this.listeners.get(evt)?.forEach(cb => cb(data));
      if (evt !== "message") this.listeners.get("message")?.forEach(cb => cb(data));
    }
  
    getConnectionStatus() { return this.isConnected; }
  }
  

// Singelton instance
export const webSocketService = new WebSocketService();
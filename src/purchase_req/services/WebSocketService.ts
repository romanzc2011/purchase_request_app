import { computeWSURL } from "../utils/ws";

class WebSocketService {
    private socket: WebSocket | null = null;
    private listeners: Map<string, ((data: any) => void)[]> = new Map();
    private queue: string[] = [];
    private heartbeatId: number | null = null;

    // ---------------------------------------------------------------
    // CONNECT
    // ---------------------------------------------------------------
    public connect() {
        // Guard against multiple connections
        if (this.socket && (
            this.socket.readyState === WebSocket.OPEN ||
            this.socket.readyState === WebSocket.CONNECTING
        )) {
            return;
        }

        this.socket = new WebSocket(computeWSURL());

        // On open send message to backend that we are connected
        this.socket.onopen = () => {
            console.log("✅ WebSocket is connected");

            // Flush queued outbound messages
            for (const msg of this.queue) this.socket!.send(msg);
            this.queue.length = 0;
            this.startHeartbeat();
            console.log("✅ WebSocket is connected");
        };

        // On MEssagees 
        this.socket.onmessage = (event) => {
            let data: any = event.data;

            if (data.type === "json") {
                data = JSON.parse(data);
            }
            this.notifyListeners(data);
        };

        this.socket.onclose = (e) => { 
            this.stopHeartbeat();
            this.disconnect();
            console.log("❌ WebSocket is disconnected, event triggered: ", e);
        }

    }

    // Send message to websocket server
    public send(payload: any) { 
        const data = JSON.stringify(payload);
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(data);
        } else {
            // Queue the message until the socket is open
            this.queue.push(data);
            if (!this.socket || this.socket.readyState === WebSocket.CLOSED) { 
                this.connect();
            }
        }
    }

    // Get Status of connection
    public getConnectionStatus(): boolean { 
        if(this.socket && this.socket.readyState === WebSocket.OPEN) {
            return true;
        }
        return false;
    }

    // ---------------------------------------------------------------
    // DISCONNECT
    // ---------------------------------------------------------------
    public disconnect() {
        if (this.socket) {
            this.socket.close()
            this.socket = null;
        }
    }

    // ---------------------------------------------------------------
    // SUBSCRIBE
    // ---------------------------------------------------------------
    public subscribe(event: string, callback: (data: any) => void) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event)!.push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(event);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index > -1) {
                    callbacks.splice(index, 1);
                }
            }
        };
    }

    // ---------------------------------------------------------------
    // NOTIFY LISTENERS
    // ---------------------------------------------------------------
    private notifyListeners(data: any) { 
        console.log("NOTIFYING LISTENERS: ", data);
        const event = data.event || 'message';
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }

    // ---------------------------------------------------------------
    // START HEARTBEAT
    // ---------------------------------------------------------------
    private startHeartbeat() {
        if (this.heartbeatId != null) return;

        this.heartbeatId = window.setInterval(() => this.send({ event:"ping" }), 25000);
      }

    // ---------------------------------------------------------------
    // STOP HEARTBEAT
    // ---------------------------------------------------------------
    private stopHeartbeat() {
        if (this.heartbeatId != null) {
            clearInterval(this.heartbeatId);
            this.heartbeatId = null;
        }
    }
}

// Singelton instance
export const webSocketService = new WebSocketService();

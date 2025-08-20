import { computeWSURL } from "../utils/ws";

class WebSocketService {
    private socket: WebSocket | null = null;
    private listeners: Map<string, ((data: any) => void)[]> = new Map();
    private isConnected = false;

    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return; // Already connected
        }

        this.socket = new WebSocket(computeWSURL());
        
        this.socket.onopen = () => {
            console.log("✅ WebSocket connected");
            this.isConnected = true;
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.notifyListeners(data);
            } catch (e) {
                console.error("Error parsing WebSocket message:", e);
            }
        };

        this.socket.onclose = () => {
            console.log("❌ WebSocket disconnected");
            this.isConnected = false;
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.isConnected = false;
        }
    }

    send(data: any) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    subscribe(event: string, callback: (data: any) => void) {
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

    private notifyListeners(data: any) {
        const event = data.event || 'message';
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }

    getConnectionStatus() {
        return this.isConnected;
    }
}

// Create singleton instance
export const webSocketService = new WebSocketService();

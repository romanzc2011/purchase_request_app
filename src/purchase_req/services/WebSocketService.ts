import { computeWSURL } from "../utils/ws";

class WebSocketService {
    private socket: WebSocket | null = null;
    private listeners: Map<string, ((data: any) => void)[]> = new Map();
    private isConnected = false;

    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;  // Already established
        }
        else if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
            console.log("🔌 Attempting WebSocket connection.");
        }

        this.socket = new WebSocket(computeWSURL("/communicate"));

        // On open send message to backend that we are connected
        this.socket.onopen = () => {
            console.log("✅ WebSocket connected");
            this.isConnected = true;
        }

    }

    disconnect() {
        if (this.socket) {
            this.socket.close()
            this.socket = null;
            this.isConnected = false;
        }
    }

    send(data: any) {
        if (this.socket && this.isConnected) {
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

    // private notifyListeners(data: any) {
    //     const event = data.event || 'message';
    //     const callbacks = this.listeners.get(event);
    //     if (callbacks) {
    //         callbacks.forEach(callback => callback(data));
    //     }
    // }

    getConnectionStatus() {
        return this.isConnected;
    }
}

// Singelton instance
export const webSocketService = new WebSocketService();

import { useEffect, useState, useRef } from "react";
import { computeWSURL } from "../utils/ws";

// #########################################################################################
// WEBSOCKETS HOOK 
// #########################################################################################
export function useWebSockets(
	onMessage?: (msg: MessageEvent) => void
) {
	const [isConnected, setIsConnected] = useState(false);
	const [socket, setSocket] = useState<WebSocket>();

	// Create the connection to backend
	useEffect(() => {
		const connectWebSocket = () => {
			const ws = new WebSocket(computeWSURL("/communicate"));
			setSocket(ws)

			// These are event listeners
			ws.onopen = (event) => {
				console.log("✅ WEBSOCKET CONNECTED ", event);
				setIsConnected(true);
			};
			
			ws.onmessage = (event) => {
				if(onMessage) {
                    onMessage(event);
                    console.log("🔴 WEBSOCKET MESSAGE RECEIVED", event);
				}
			}

			ws.onclose = (event) => {
				console.log("❌ WEBSOCKET DISCONNECTED", event.code, event.reason);
				setIsConnected(false);
			};

			ws.onerror = (err) => {
				console.log("⚠️ WEBSOCKET ERROR", err);
			}
		};

		connectWebSocket();

	}, [WEBSOCKET_URL]); // Removed onMessage from dependencies to prevent reconnections

	return {
		socket,
		isConnected
	}
}

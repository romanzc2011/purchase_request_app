import { useEffect, useState, useRef } from "react";
// import { isDownloadSig } from "../utils/PrasSignals";

// #########################################################################################
// WEBSOCKETS HOOK 
// #########################################################################################
export function useWebSockets(
	WEBSOCKET_URL: string, 
	onMessage?: (msg: MessageEvent) => void
) {
	const [isConnected, setIsConnected] = useState(false);
	const [socket, setSocket] = useState<WebSocket>();
	const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
	const reconnectAttemptsRef = useRef(0);
	const maxReconnectAttempts = 5;
	const baseReconnectDelay = 1000; // 1 second

	// Create the connection to backend
	useEffect(() => {
		const connectWebSocket = () => {
			const ws = new WebSocket(WEBSOCKET_URL);
			setSocket(ws)

			// These are event listeners
			ws.onopen = (event) => {
				console.log("✅ WEBSOCKET CONNECTED ", event);
				setIsConnected(true);
				reconnectAttemptsRef.current = 0; // Reset reconnect attempts on successful connection
				ws.send('HELO SERVER');
			};
			
			ws.onmessage = (event) => {
				if(onMessage) {
					onMessage(event);
				}
			}

			ws.onclose = (event) => {
				console.log("❌ WEBSOCKET DISCONNECTED", event.code, event.reason);
				setIsConnected(false);
				
				// Attempt to reconnect if not a normal closure
				if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
					const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
					console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
					
					reconnectTimeoutRef.current = setTimeout(() => {
						reconnectAttemptsRef.current++;
						connectWebSocket();
					}, delay);
				}
			};

			ws.onerror = (err) => {
				console.log("⚠️ WEBSOCKET ERROR", err);
			}
		};

		connectWebSocket();

		return () => {
			if (reconnectTimeoutRef.current) {
				clearTimeout(reconnectTimeoutRef.current);
			}
			if (socket) {
				socket.close();
			}
		};
	}, [WEBSOCKET_URL]); // Removed onMessage from dependencies to prevent reconnections

	return {
		socket,
		isConnected
	}
}
import { useEffect, useState } from "react";

// #########################################################################################
// WEBSOCKETS HOOK 
// #########################################################################################
export function useWebSockets(
	WEBSOCKET_URL: string, 
	onMessage?: (msg: MessageEvent) => void
) {
	const [isConnected, setIsConnected] = useState(false);
	const [socket, setSocket] = useState<WebSocket>();

	// Create the connection to backend
	useEffect(() => {
		const ws = new WebSocket(WEBSOCKET_URL);
		setSocket(ws)

		// These are event listeners
		ws.onopen = (event) => {
			console.log("✅ WEBSOCKET CONNECTED ", event);
			setIsConnected(true);
			ws.send('HELO SERVER');
		};
		
		ws.onmessage = (event) => {
			console.log("📨 WEBSOCKET DATA: ", event.data);
			console.log("ws.onmessage datatype: ", typeof(event));
			console.log("WEBSOCKET RAW DATA: ", event);
			if(onMessage) {
				onMessage(event);
			}
		}

		ws.onclose = () => {
			console.log("❌ WEBSOCKET DISCONNECTED");
			setIsConnected(false);
		};

		ws.onerror = (err) => {
			console.log("⚠️ WEBSOCKET ERROR", err);
		}

		return () => ws.close();
	}, [WEBSOCKET_URL, onMessage]);

	return {
		socket,
		isConnected
	}
}
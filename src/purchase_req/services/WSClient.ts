import { computeWSURL } from "../utils/misc_utils";

const ws = new WebSocket(computeWSURL("/communicate"));

ws.onopen = () => {
    console.log("Connected to WebSocket server");
    ws.send(JSON.stringify({ event: "HELO" }));
};

ws.onmessage = (event: MessageEvent) => {
    console.log(`Received message from server: ${event.data}`);
};

ws.onclose = () => {
    console.log("Disconnected from WebSocket server");
}

ws.onerror = (error: Event) => {
    console.error("Websocket error: ", error);
}
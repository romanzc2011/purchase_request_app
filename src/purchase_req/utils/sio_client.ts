import { io } from "socket.io-client";

export function computeWSURL(path?: string) { 
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const  p = path?.startsWith("/") ? path : `/${path}`;
    return `${wsProto}//${host}${p}`;
}

export function computeHTTPURL(path: string) { 
    const proto = window.location.protocol;
    const host = window.location.host;
    const p = path.startsWith("/") ? path : `/${path}`;
    return `${proto}//${host}${p}`;
}

const socket = io(computeWSURL(), { path: "/realtime/communicate" });

socket.on("connect", () => {
    socket.emit("HELO");
    console.log("🔌 WebSocket connected");
});
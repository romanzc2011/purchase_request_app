import { io } from "socket.io-client";

export function computeWSURL(path?: string) { 
    const { protocol, hostname } = window.location;
    const port: number = 5004;
    console.log("🔌 COMPUTE WS URL protocol", protocol);
    console.log("🔌 COMPUTE WS URL hostname", hostname);
    
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    const base = `${wsProto}//${hostname}:${port}`;
    const fullPath = path ? path : "";
    console.log("SOCKETIO: ", base + fullPath);
    return base + fullPath;
}

export function computeHTTPURL(path: string) { 
    const isHTTPS = window.location.protocol === "https:";
    const proto = isHTTPS ? "https:" : "http:"; // ✅ Add the missing colon
    const hostname = window.location.hostname;
    const port = window.location.port;
    const p = path.startsWith("/") ? path : `/${path}`;
    const fullHost = port ? `${hostname}:${port}` : hostname;
    console.log("�� COMPUTE HTTP URL", `${proto}//${fullHost}${p}`);
    return `${proto}//${fullHost}${p}`;
}

const socket = io(computeWSURL(), { path: "/realtime/communicate" });

socket.on("connect", () => {
    socket.emit("HELO");
    console.log("🔌 WebSocket connected");
});
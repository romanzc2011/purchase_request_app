import { io } from "socket.io-client";

export function computeWSURL(path?: string) { 
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const p = path?.startsWith("/") ? path : `/${path}`;
    console.log("🔌 COMPUTE WS URL", `${wsProto}//${host}${p}`);
    return `${wsProto}//${host}${p}`;
}

export function computeHTTPURL(path: string) {
    const proto = window.location.protocol;
    const host = window.location.host;
    const p = path.startsWith("/") ? path : `/${path}`;
    console.log("🔌 COMPUTE HTTP URL", `${proto}//${host}${p}`);
    return `${proto}//${host}${p}`;
}

const socket = io(computeWSURL("/realtime/communicate"), { path: "/realtime/communicate" });

socket.on("connect", () => {
  console.log("🔌 connected");
});
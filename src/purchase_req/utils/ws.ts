export function computeWSURL(path = "/communicate") { 
    const { protocol, host } = window.location;
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    const base = `${wsProto}//${host}`;
    console.log("🔌 COMPUTE WS URL", `${base}${path.startsWith("/") ? path : `/${path}`}`);
    return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export function computeHTTPURL(path: string) { 
    const isHTTPS = window.location.protocol === "https:";
    const proto = isHTTPS ? "https:" : "http:";
    const p = path.startsWith("/") ? path : `/${path}`;
    console.log("🔌 COMPUTE HTTP URL", `${proto}//${window.location.host}${p}`);
    return `${proto}//${window.location.host}${p}`;
}
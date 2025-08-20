export function computeWSURL(path = "/communicate") { 
    const { protocol, host } = window.location;
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    const base = `${wsProto}//${host}`;
    const fullUrl = `${base}${path.startsWith("/") ? path : `/${path}`}`;
    console.log("🔌 COMPUTE WS URL", fullUrl);
    return fullUrl;
}

export function computeHTTPURL(path: string) { 
    const isHTTPS = window.location.protocol === "https:";
    const proto = isHTTPS ? "https:" : "http:";
    const p = path.startsWith("/") ? path : `/${path}`;
    console.log("🔌 COMPUTE HTTP URL", `${proto}//${window.location.host}${p}`);
    return `${proto}//${window.location.host}${p}`;
}
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
    // Use API port 5004 instead of frontend port 5002
    const apiHost = window.location.hostname + ":5004";
    console.log("🔌 COMPUTE HTTP URL", `${proto}//${apiHost}${p}`);
    return `${proto}//${apiHost}${p}`;
}

export async function fetchUsernames(query: string): Promise<string[]> {
    try {
        const response = await fetch(`${computeHTTPURL("/api/usernames")}?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Error fetching usernames:', error);
        return [];
    }
}
export function computeWSURL(path = "/communicate") { 
    const { host } = window.location;
    const wsProto = "ws:";
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
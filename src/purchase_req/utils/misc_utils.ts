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
    return `${proto}//${host}${p}`;
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
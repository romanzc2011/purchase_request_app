export function computeAPIURL(path: string) {
    return `${window.location.origin}${path}`;
}

// WebSocket URL function removed - using SSE instead

export async function fetchUsernames(query: string): Promise<string[]> {
    try {
        const response = await fetch(`${computeAPIURL("/api/usernames")}?q=${encodeURIComponent(query)}`);
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

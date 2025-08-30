export function computeAPIURL(path: string) {
    return `${window.location.origin}${path}`;
}

export function computeWSURL(path: string) {
    return window.location.origin.replace(/^http/, 'ws') + path;
}

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
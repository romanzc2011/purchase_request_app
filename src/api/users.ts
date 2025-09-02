import { computeHTTPURL } from "../purchase_req/utils/sio_client";

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
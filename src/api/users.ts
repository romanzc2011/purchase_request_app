export async function fetchUsernames(query: string): Promise<string[]> {
    try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/usernames?q=${encodeURIComponent(query)}`);
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
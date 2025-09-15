export class APIError extends Error { 
    constructor(
        message: string,
        public statusCode: number,
        public code?: number,
    ) {
        super(message);
    }
}

export async function handleAPIError(response: Response) { 
    if (!response.ok) { 
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
            errorData.message || `HTTP ${response.status}`,
            response.status,
            errorData.code,
        );
    }
}

// Example usage functions
export async function fetchWithErrorHandling(url: string, options: RequestInit = {}) {
    try {
        const response = await fetch(url, options);
        await handleAPIError(response); // This will throw if response is not ok
        return await response.json();
    } catch (error) {
        if (error instanceof APIError) {
            // Handle specific API errors
            console.error(`API Error ${error.statusCode}: ${error.message}`);
            throw error; // Re-throw to let caller handle
        }
        // Handle network errors, timeouts, etc.
        console.error('Network error:', error);
        throw new APIError('Network error occurred', 0);
    }
}

// Example: Using fetchWithErrorHandling in a service
export async function fetchUsernamesWithErrorHandling(query: string): Promise<string[]> {
    try {
        const token = localStorage.getItem("access_token");
        const data = await fetchWithErrorHandling(
            `/api/usernames?q=${encodeURIComponent(query)}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            }
        );
        return Array.isArray(data) ? data : [];
    } catch (error) {
        if (error instanceof APIError) {
            if (error.statusCode === 401) {
                // Handle token expiration
                localStorage.removeItem("access_token");
                window.location.href = "/login";
            }
        }
        throw error;
    }
}
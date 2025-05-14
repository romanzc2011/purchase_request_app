export async function addComment(UUID: string, comment: string) {
    try {
        console.log("Making API call to:", `${import.meta.env.VITE_API_URL}/api/add_comment/${UUID}`);
        console.log("With payload:", { comment: comment.trim() });
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/add_comment/${UUID}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
            body: JSON.stringify({ comment: comment.trim() }),
        });
        console.log("Response status:", response.status);
        const data = await response.json();
        console.log("Response data:", data);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error("Error adding comment:", error);
        throw error;
    }
}   
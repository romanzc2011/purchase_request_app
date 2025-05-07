import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

const API_URL_COMMENT = `${import.meta.env.VITE_API_URL}/api/add_comment`;

// #####################################################################################
// COMMENT API
// #####################################################################################
export const addComment = async (ID: string, comment: string) => {
    console.log("Making API call to:", `${API_URL_COMMENT}/${ID}`);
    console.log("With payload:", { comment: comment.trim() });
    
    const response = await fetch(`${API_URL_COMMENT}/${ID}`, {
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
    
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    return data;
}; 

// #####################################################################################
// COMMENT MUTATION
// #####################################################################################
export const useCommentMutation = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ ID, comment }: { ID: string; comment: string }) => addComment(ID, comment),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
            toast.success("Comment added");
        },
        onError: () => toast.error("Failed to add comment"),
    });
};
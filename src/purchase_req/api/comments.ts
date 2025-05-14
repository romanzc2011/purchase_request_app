import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

const API_URL_COMMENT = `${import.meta.env.VITE_API_URL}/api/add_comment`;

// #####################################################################################
// COMMENT API
// #####################################################################################
export const addComment = async (UUID: string, comment: string) => {
    const currentDate = new Date().toISOString();
    console.log("Making API call to:", `${API_URL_COMMENT}/${UUID}`);
    console.log("With payload:", { comment: comment.trim(), date: currentDate });
    
    const response = await fetch(`${API_URL_COMMENT}/${UUID}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ 
            comment: comment.trim(),
            date: currentDate 
        }),
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
        mutationFn: ({ UUID, comment }: { UUID: string; comment: string }) => addComment(UUID, comment),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["approvalData"] });
            toast.success("Comment added");
        },
        onError: () => toast.error("Failed to add comment"),
    });
};
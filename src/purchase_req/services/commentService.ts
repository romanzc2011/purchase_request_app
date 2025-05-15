import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

const API_URL_ADD_COMMENT = `${import.meta.env.VITE_API_URL}/api/add_comment`
const API_URL_ADD_COMMENTS_BULK = `${import.meta.env.VITE_API_URL}/api/add_comments_bulk`

export async function addComment(uuid: string, comment: string): Promise<void> {
    try {
        const response = await fetch(`${API_URL_ADD_COMMENT}/${uuid}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ comment }),
        });

        if (!response.ok) {
            throw new Error(`Failed to add comment: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        throw error;
    }
} 

export async function addCommentsBulk(
    comments: { uuid: string; comment: string }[]
  ): Promise<void> {
    const payload = { comments, count: comments.length };
    const response = await fetch(`${API_URL_ADD_COMMENTS_BULK}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const err = await response.json();
        console.error('Error response:', err);
        throw new Error(`Failed to add comments: ${response.statusText}`);
    }
}

//####################################################################
// USE COMMENT MUTATION
//####################################################################
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
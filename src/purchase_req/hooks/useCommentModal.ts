import { useState, useCallback } from "react";
import { addComment } from "../api/comments";
import { toast } from "react-toastify";

export function useCommentModal() {
    // Internal State
    const [isOpen, setIsOpen] = useState(false);  // Modal open/close state
    const [modalRowId, setModalRowId] = useState<string | null>(null); // ID of row being commented on
    const [commentText, setCommentText] = useState(""); // Comment input text

    // Open the modal for a specific row
    const open = useCallback((rowId: string) => {
        setModalRowId(rowId);
        setCommentText("");
        setIsOpen(true);
    }, []);

    // Close the modal
    const close = useCallback(() => {
        setIsOpen(false);
        setModalRowId(null);
        setCommentText("");
    }, []);

    // #####################################################################################
    // Handle comment submission
    const handleSubmit = useCallback(async (comment: string) => {
        console.log("handleSubmit called with:", { modalRowId, comment });
        if (!modalRowId || !comment.trim()) {
            console.log("Early return - missing modalRowId or empty comment");
            return;
        }

        try {
            console.log("Calling addComment with:", { modalRowId, comment });
            await addComment(modalRowId, comment);
            toast.success("Comment added successfully");
            close();
        } catch (error) {
            console.error("Error adding comment:", error);  
            toast.error("Failed to add comment");
        }
    }, [modalRowId, close]);

    return {
        isOpen,
        commentText,
        setCommentText,
        open,
        close,
        handleSubmit,
    };
}
import { useState, useCallback } from "react";
import { addComment, addCommentsBulk } from "../services/CommentService";
import { toast } from "react-toastify";

export function useCommentModal() {
    const [isOpen, setIsOpen] = useState(false);
    const [modalRowId, setModalRowId] = useState<string | null>(null);
    const [commentText, setCommentText] = useState("");
    const [resolver, setResolver] = useState<((comment: string) => void) | null>(null);
    const [isBulkMode, setIsBulkMode] = useState(false);
    const [bulkUuids, setBulkUuids] = useState<string[]>([]);

    // Open the modal for a single row
    const open = useCallback((rowId: string) => {
        setModalRowId(rowId);
        setCommentText("");
        setIsOpen(true);
        setIsBulkMode(false);
        return new Promise<string>((resolve) => {
            setResolver(() => resolve);
        });
    }, []);

    // Open the modal for bulk comments
    const openBulk = useCallback((uuids: string[]) => {
        setBulkUuids(uuids);
        setCommentText("");
        setIsOpen(true);
        setIsBulkMode(true);
        return new Promise<string>((resolve) => {
            setResolver(() => resolve);
        });
    }, []);

    const close = useCallback(() => {
        setIsOpen(false);
        setModalRowId(null);
        setCommentText("");
        setResolver(null);
        setIsBulkMode(false);
        setBulkUuids([]);
    }, []);

    const handleSubmit = useCallback(async (comment: string) => {
        if (!comment.trim()) {
            console.log("Early return - empty comment");
            return;
        }

        try {
            if (isBulkMode) {
                // Handle bulk comments
                const comments = bulkUuids.map(uuid => ({
                    uuid,
                    comment
                }));
                await addCommentsBulk(comments);
                toast.success("All comments added successfully");
            } else {
                // Handle single comment
                if (!modalRowId) return;
                console.log("modalRowId", modalRowId);
                await addComment(modalRowId, comment);
                console.log("Comment added successfully single");
                toast.success("Comment added successfully");
            }
            
            resolver?.(comment);
            close();
        } catch (error) {
            console.error("Error adding comment:", error);
            toast.error("Failed to add comment");
        }
    }, [modalRowId, bulkUuids, isBulkMode, resolver, close]);

    return {
        isOpen,
        commentText,
        setCommentText,
        open,
        openBulk,
        close,
        handleSubmit,
        isBulkMode
    };
}
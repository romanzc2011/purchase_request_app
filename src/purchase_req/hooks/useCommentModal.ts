import { useState, useCallback } from "react";

/**
 * Hook to manage the state and behavior of a comment modal.
 * @param onSubmitBackend - function to call when submitting a comment: (rowId, comment) => Promise<any>
 */

export function useCommentModal(
    onSubmitBackend: (rowId: string, comment: string) => Promise<any>
) {
    const [isOpen, setIsOpen] = useState(false);
    const [modalRowId, setModalRowId] = useState<string | null>(null);

    // OPpen modal for specific row ID
    const open = useCallback((rowId: string) => {
        setModalRowId(rowId);
        setIsOpen(true);
    }, []);

    // Close modal and clear the row ID
    const close = useCallback(() => {
        setModalRowId(null);
        setIsOpen(false);
    }, []);

    // Handle form submission: call backend and close modal
    const handleSubmit = useCallback(
        async (comment: string) => {
            if (!modalRowId) return;
            try {
                await onSubmitBackend(modalRowId, comment);
                close();
            } catch (error) {
                console.error("Error submitting comment:", error);
            }
        },
        [modalRowId, onSubmitBackend, close]
    );

    return { isOpen, modalRowId, open, close, handleSubmit };
}
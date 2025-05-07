/**
 * useCommentModal.ts
 * Author: Roman Campbell
 * Date: 2025-05-07
 * 
 * Purpose: Custom hook that manages the state and logic for comment modals across the application.
 * 
 * Connection in Comment System:
 * - Central piece that connects UI (AddComment) with data handling (ApprovalTable)
 * - Manages modal state and comment submission flow
 * - Provides consistent comment handling across different parts of the app
 * 
 * Flow:
 * 1. Hook is initialized with a backend submission function
 * 2. Manages modal open/close state and current row being commented on
 * 3. When comment is submitted:
 *    - Validates rowId exists
 *    - Calls provided backend function
 *    - Handles success/error states
 *    - Closes modal on success
 * 
 * Returns:
 * - isOpen: boolean - Current modal visibility state
 * - modalRowId: string | null - ID of row being commented on
 * - open: (rowId: string) => void - Function to open modal for specific row
 * - close: () => void - Function to close modal
 * - handleSubmit: (comment: string) => void - Function to handle comment submission
 */

import { useState, useCallback } from "react";

export function useCommentModal(
    onSubmitBackend: (rowId: string, comment: string) => Promise<any>
) {
    const [isOpen, setIsOpen] = useState(false);
    const [modalRowId, setModalRowId] = useState<string | null>(null);

    // Open modal for specific row ID
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
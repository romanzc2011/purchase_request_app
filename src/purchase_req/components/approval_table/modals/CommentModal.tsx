/**
 * CommentModal.tsx
 * Author: Roman Campbell
 * Purpose: A reusable modal component that provides the UI for adding and editing comments.
 * 
 * Connection in Comment System:
 * - Primary UI component for comment input
 * - Used by ApprovalTable to display comment interface
 * - Receives state management from useCommentModal hook
 * 
 * Features:
 * - Handles comment text input and state
 * - Provides submit and cancel actions
 * - Resets comment state when modal opens/closes
 * - Maintains comment state between edits
 * 
 * Flow:
 * 1. Modal opens with optional initial value
 * 2. User can type/edit comment
 * 3. On submit: passes comment to parent and clears input
 * 4. On cancel: closes modal and resets to initial value
 */

import { useState, useEffect } from 'react';
import { Box, Typography, Button, Modal, TextField } from '@mui/material';

export interface CommentModalProps {
    open: boolean;
    commentText?: string;
    onClose: () => void;
    onSubmit: (value: string) => void;
}

export default function CommentModal({
    open,
    commentText,
    onClose,
    onSubmit }: CommentModalProps) {

    const [comment, setComment] = useState(commentText ?? "");

    // Reset comment when initialValue or open changes   
    useEffect(() => {
        if (open) {
            setComment(commentText ?? "");
        }
    }, [open, commentText]);

    const handleSubmit = () => {
        onSubmit(comment);
        setComment("");
    };

    const handleCancel = () => {
        onClose();
        setComment(commentText ?? "");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <Modal
            open={open}
            onClose={handleCancel}
            aria-labelledby="justification-modal"
            aria-describedby="full-justification"
        >
            <Box sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 700,
                bgcolor: '#2c2c2c',
                border: '2px solid #800000',
                boxShadow: 24,
                p: 4,
                borderRadius: 1,
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
            }}>
                <Typography id="comment-modal-title" variant="h6">
                    Add Comment
                </Typography>
                <form onSubmit={(e) => {
                    e.preventDefault();
                    handleSubmit();
                }}>
                    <TextField
                        fullWidth
                        multiline
                        rows={4}
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        onKeyDown={handleKeyDown}
                        sx={{
                            // style the OutlinedInput root
                            "& .MuiOutlinedInput-root": {
                                backgroundColor: "#ffffff",      // make the fill white
                                "& fieldset": {
                                    borderColor: "white",          // keep your white border
                                },
                                "&:hover fieldset": {
                                    borderColor: "gray",
                                },
                                "&.Mui-focused fieldset": {
                                    borderColor: "white",
                                },
                                // style the actual text slot (works for both <input> and <textarea>)
                                "& .MuiOutlinedInput-input": {
                                    color: "black",                // black text on white background
                                },
                            },
                            // style the label too
                            "& .MuiInputLabel-root": {
                                color: "white",
                            },
                        }}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                        <Button
                            type="button"
                            onClick={handleCancel}
                            variant="contained"
                            sx={{ mt: 3, bgcolor: '#800000', '&:hover': { bgcolor: '#600000' } }}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            variant="contained"
                            sx={{ mt: 3, bgcolor: '#800000', '&:hover': { bgcolor: '#600000' } }}
                            onClick={(e) => {
                                e.preventDefault();
                                onSubmit(comment);  // this calls handleSubmit(comment) from the hook
                            }}
                        >
                            Submit
                        </Button>
                    </Box>
                </form>
            </Box>
        </Modal>
    );
}

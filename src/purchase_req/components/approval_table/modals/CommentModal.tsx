import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Modal, TextField } from '@mui/material';

export interface CommentModalProps {
    open: boolean;
    initialValue?: string;
    onClose: () => void;
    onSubmit: (value: string) => void;
}

export default function CommentModal({
    open,
    initialValue = "",
    onClose,
    onSubmit }: CommentModalProps) {

    const [comment, setComment] = useState(initialValue);

    // Reset comment when initialValue or open changes   
    useEffect(() => {
        if (open) {
            setComment(initialValue);
        }
    }, [open, initialValue]);

    const handleSubmit = () => {
        onSubmit(comment);
        setComment("");
    };

    const handleCancel = () => {
        onClose();
        setComment(initialValue);
    };

    return (
        <Modal
            open={open}
            onClose={handleCancel}
            aria-labelledby="comment-modal"
        >
            <Box
                sx={{
                    position: 'absolute' as const,
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 400,
                    bgcolor: 'background.paper',
                    boxShadow: 24,
                    p: 4,
                    borderRadius: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                }}
            >
                <Typography id="comment-modal-title" variant="h6">
                    Add Comment
                </Typography>
                <TextField
                    fullWidth
                    multiline
                    rows={4}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                    <Button onClick={handleCancel}>Cancel</Button>
                    <Button onClick={handleSubmit} variant="contained">Submit</Button>
                </Box>
            </Box>
        </Modal>
    );
}

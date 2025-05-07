import { Box, Typography, Button, Modal, TextField } from "@mui/material";
import { useState } from "react";

type CommentModalProps = {
    open: boolean;
    initialValue?: string;
    onClose: () => void;
    onSubmit: (value: string) => void;
}

export default function CommentModal({ open, initialValue, onClose, onSubmit }: CommentModalProps) {
    const [comment, setComment] = useState(initialValue || "");

    const handleSubmit = () => {
        onSubmit(comment);
    }

    return (
        <Modal
            open={open}
            onClose={onClose}
            aria-labelledby="comment-modal"
        >
            <Box sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 400,
                bgcolor: 'background.paper',
                boxShadow: 24,
                p: 4,
                borderRadius: 1
            }}>
                <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
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
                    <Button onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} variant="contained">Submit</Button>
                </Box>
            </Box>
        </Modal>
    );
}
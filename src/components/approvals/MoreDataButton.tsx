import { useState } from "react";
import MoreIcon from '@mui/icons-material/More';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Modal from '@mui/material/Modal';
/*************************************************************************************/
/* MoreDataButton simply the MORE icons in ApprovalTable for itemDescription and
   justification. Not enough room in table so this way they can see all the data */
/*************************************************************************************/
interface MoreDataButtonProps {
    name: string;
    data: string;
}

/* Style for button */
const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 800,
    bgcolor: '#212528',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
};

function MoreDataButton({ name, data }: MoreDataButtonProps) {
    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    return (
        <div>
            <IconButton sx={{ color: "white" }} onClick={handleOpen}>
                <MoreIcon />
            </IconButton>
            <Modal
                open={open}
                onClose={handleClose}
                aria-labelledby="title"
                aria-describedby="description"
            >
                <Box sx={style}>
                    <Typography id="title" variant="h6" component="h2">
                        {name}
                    </Typography>
                    <Typography id="description" sx={{ mt: 2, whiteSpace: 'normal', wordBreak: 'break-word' }}>
                        {data}
                    </Typography>
                    <Button onClick={handleClose} sx={{ mt: 2 }}>
                        Close
                    </Button>
                </Box>
            </Modal>
        </div>
    )
}

export default MoreDataButton;
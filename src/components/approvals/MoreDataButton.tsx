import MoreIcon from '@mui/icons-material/More';
import IconButton from '@mui/material/IconButton';

function MoreDataButton() {

    const handleClick = () => {
        console.log("More clicked!");
    };

    return (
        <IconButton sx={{ color: "white" }} onClick={handleClick}>
            <MoreIcon />
        </IconButton>
    )
}

export default MoreDataButton;
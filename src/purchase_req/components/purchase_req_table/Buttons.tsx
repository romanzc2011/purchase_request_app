import React from 'react'
import { Button as MuiButton } from '@mui/material'
import "../../styles/ApprovalTable.css"

interface ButtonProps {
	label: string;
	className?: string;
	disabled?: boolean;
	onClick?: React.MouseEventHandler<HTMLButtonElement>;
}

// Define button component
const Buttons: React.FC<ButtonProps> = ({ label, className, disabled, onClick }) => {
	return (
		<MuiButton
			disabled={disabled}
			className={className || "assign-button"}
			onClick={onClick}
			variant="contained"
			sx={{
				fontFamily: "'Play', sans-serif !important",
				textTransform: 'none',
				backgroundColor: 'maroon',
				fontSize: '1.15rem',
				'&:hover': {
					backgroundColor: 'darkred'
				},
				'& .MuiButtonBase-root': {
					fontFamily: "'Play', sans-serif !important"
				}
			}}
		>
			{label}
		</MuiButton>
	);
};

export default Buttons;
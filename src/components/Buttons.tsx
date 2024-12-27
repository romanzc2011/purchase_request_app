import React from 'react'

interface ButtonProps {
    label: string;
    className?: string;
    disabled?: boolean;
    onClick?: React.MouseEventHandler<HTMLButtonElement>;
}

// Define button component
const Buttons: React.FC<ButtonProps> = ({ label, className, disabled, onClick }) => {
  return (
    <button disabled={disabled} className={className || "btn btn-primary me-3"} onClick={ onClick }>
        {label}
    </button>
  );
};

export default Buttons;
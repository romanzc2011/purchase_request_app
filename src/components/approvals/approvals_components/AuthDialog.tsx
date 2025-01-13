import React, { useState } from "react";
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Typography,
} from "@mui/material";

type UserCreds = {
    username: string;
    password: string;
}

interface AuthDialogProps {
    credentials: UserCreds[];
    open: boolean;
    onClose: () => void;
    onAuth: (username: string, password: string) => void;
}

const AuthDialog = ({ open, onClose, onAuth }) => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleLogin = () => {
        if(!username || !password) {
            setError("Both fields are required.");
            return;
        };     

        if(username && password) {

        };

    }


}
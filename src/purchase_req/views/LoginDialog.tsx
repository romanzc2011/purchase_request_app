import { useState } from "react";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import { Box, CircularProgress } from "@mui/material";
import BKSeal from "../../assets/seal_no_border.png";
import { toast } from "react-toastify";
import { computeHTTPURL } from "../utils/sio_client";

interface LoginDialogProps {
    open: boolean;
    onClose: () => void;
    onLoginSuccess: (ACCESS_GROUP: boolean, CUE_GROUP: boolean, IT_GROUP: boolean) => void;
}

export default function LoginDialog({
    open,
    onClose,
    onLoginSuccess,
}: LoginDialogProps) {
    const [username, setUsername] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);

    const API_URL = computeHTTPURL("/api/login");

    /***********************************************************************/
    /* VALIDATE INPUT */
    /***********************************************************************/
    const validateInput = (): boolean => {
        if (!username || !password) {
            setError("Username and password are required");
            return false;
        }
        setError("");
        return true;
    };

    /***********************************************************************/
    /* HANDLE LOGIN */
    /***********************************************************************/
    async function handleLogin(username: string, password: string) {
        const form = new URLSearchParams();
        form.append("username", username);
        form.append("password", password);

        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: form.toString(),
        });

        if (!response.ok) {
            const err = await response.text();
            toast.error("Login failed: " + err);
            throw new Error(`Login status ${response.status}`);
        }

        const text = await response.text();
        if (!text) {
            throw new Error("No data received from server");
        }

        let data;
        try {
            data = JSON.parse(text);
        } catch (error) {
            throw new Error("Invalid JSON data received from server");
        }

        if (!data || !data.access_token || !data.user) {
            throw new Error("Login response is missing required fields");
        }

        const { access_token, token_type, user } = data;

        localStorage.setItem("access_token", access_token);
        localStorage.setItem("token_type", token_type);
        localStorage.setItem("user", JSON.stringify(user));
        onLoginSuccess(user.ACCESS_GROUP, user.CUE_GROUP, user.IT_GROUP);
        console.log("Login successful");
        toast.success("Login successful");

        onClose();

        return data;
    }

    /***********************************************************************/
    /* HANDLE SUBMIT */
    /***********************************************************************/
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateInput()) return;

        setLoading(true);
        try {
            const { access_token, user } = await handleLogin(username, password);
            localStorage.setItem("access_token", access_token);
            onLoginSuccess(user.ACCESS_GROUP, user.CUE_GROUP, user.IT_GROUP);
        } catch (error) {
            setLoading(false);
        }
    };

    return (
        <Dialog sx={{ background: "#2c2c2c" }} open={open} onClose={onClose}>

            <form onSubmit={handleSubmit}>
                <DialogTitle
                    sx={{
                        background: "linear-gradient(to bottom, #2c2c2c, #800000)",
                        color: "white",
                    }}
                >
                    Login
                </DialogTitle>
                <DialogContent
                    sx={{
                        background: " #2c2c2c",
                        color: "white",
                    }}
                >
                    <DialogContentText sx={{ color: "white" }}>
                        Please enter your username and password to log in.
                    </DialogContentText>

                    <Box sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                        mt: 2
                    }}>
                        {/* Seal on the left */}
                        <Box sx={{
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            minWidth: 120,
                        }}>
                            <img
                                src={BKSeal}
                                style={{ height: "140px" }}
                                alt="Seal"
                            />
                        </Box>

                        {/* Form fields on the right */}
                        <Box sx={{ flex: 1 }}>
                            {/* USERNAME INPUT */}
                            <TextField
                                margin="dense"
                                type="text"
                                fullWidth
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                sx={{
                                    input: { color: "white" }, // Input text color
                                    "& .MuiInputLabel-root": { color: "white" }, // Label color
                                    "& .MuiOutlinedInput-root": {
                                        "& fieldset": {
                                            borderColor: "white", // Default border color
                                        },
                                        "&:hover fieldset": {
                                            borderColor: "gray", // Border color on hover
                                        },
                                        "&.Mui-focused fieldset": {
                                            borderColor: "white", // Border color when focused
                                        },
                                    },
                                }}
                            />

                            {/* PASSWORD INPUT */}
                            <TextField
                                margin="dense"
                                type="password"
                                fullWidth
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                sx={{
                                    input: { color: "white" }, // Input text color
                                    "& .MuiInputLabel-root": { color: "white" }, // Label color
                                    "& .MuiOutlinedInput-root": {
                                        "& fieldset": {
                                            borderColor: "white", // Default border color
                                        },
                                        "&:hover fieldset": {
                                            borderColor: "gray", // Border color on hover
                                        },
                                        "&.Mui-focused fieldset": {
                                            borderColor: "white", // Border color when focused
                                        },
                                    },
                                }}
                            />
                            {error && <p style={{ color: "red" }}>{error}</p>}
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions
                    sx={{
                        background: " #2c2c2c",
                        color: "white",
                    }}
                >
                    <Button sx={{ color: "white" }} onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit" sx={{ color: "white" }} disabled={loading}>
                        {loading ? <CircularProgress size={20} /> : "Login"}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
}
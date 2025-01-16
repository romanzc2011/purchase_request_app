import React, { useState } from "react";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

type UserCreds = {
  username: string;
  password: string;
};

interface LoginDialogProps {
  credentials?: UserCreds[];
  open: boolean;
  onClose: () => void;
  onLogin: (username: string, password: string) => void;
}

export default function LoginDialog({
  open,
  onClose,
  onLogin,
}: LoginDialogProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    if (!username || !password) {
      setError("Both fields are required.");
      return;
    }

    /* Use onLogin to get credentials */
    onLogin(username, password);

    /* Clear state and close dialog */
    setUsername("");
    setPassword("");
    setError("");
    onClose();
  };

  return (
    <Dialog sx={{ background: "#2c2c2c" }} open={open} onClose={onClose}>
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

        {/* USERNAME INPUT */}
        <TextField
          autoFocus
          margin="dense"
          label="Username"
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
          label="Password"
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
        <Button sx={{ color: "white" }} onClick={handleLogin}>
          Login
        </Button>
      </DialogActions>
    </Dialog>
  );
}

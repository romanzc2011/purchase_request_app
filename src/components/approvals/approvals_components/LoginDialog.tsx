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
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Login</DialogTitle>
      <DialogContent>
        <DialogContentText>
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
        />

        {/* PASSWORD INPUT */}
        <TextField
          margin="dense"
          label="Password"
          type="password"
          fullWidth
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleLogin}>Login</Button>
      </DialogActions>
    </Dialog>
  );
}


import { useState } from "react";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import { CircularProgress } from "@mui/material";

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

  const baseURL = "http://localhost:5004"
  const API_CALL = "/api/login";
  const API_URL = `${baseURL}${API_CALL}`
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
  const handleLogin = async () => {
    if (!validateInput()) return;

    setLoading(true);

    console.log("api: ", API_URL);
    try {
      // PROD
      
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Response Error Body:", errorText);

        throw new Error(`HTTPS error, Status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response from API: ", data);

      // Extract Groups from AD_groups and pass them
      onLoginSuccess(data.AD_Groups.ACCESS_GROUP, data.AD_Groups.CUE_GROUP, data.AD_Groups.IT_GROUP);

      // Store token in local storage
      const accessToken = data.access_token;
      
      if(accessToken) {

        localStorage.setItem("access_token", accessToken);
      } else {

        console.log("Access token not found in response")
      }
    } catch (error) {

      console.error("Error sending login request: ", error);
      setError("Login failed. Please check your credentials.");

    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin();
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
          <Button type="submit" sx={{ color: "white" }} disabled={loading}>
            {loading ? <CircularProgress size={20} /> : "Login"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

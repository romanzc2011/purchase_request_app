import { StrictMode, useState } from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import LoginDialog from "./components/approvals/approvals_components/LoginDialog.tsx";

function Root() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginAttempted, setLoginAttempted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = (username: string, password: string) => {
    console.log(`Username: ${username}, Password: ${password}`);

    /* ADD AUTH LOGIC HERE */
    /* Login was attempted but we dont know if they are authenticated yet */
    setLoginAttempted(true);
    const isAuthenticated = username !== "" && password !== "";
  }

  return (
    /********************************************************************/
    /* Determine first if user is logged in then display app */
    /********************************************************************/
    <StrictMode>
      <Router>
        {isLoggedIn ? ( /* If logged in then show App if not then display LoginDialog */
          <App />
        ) : (
          <LoginDialog
            open={!isLoggedIn}
            onClose={() => console.log("HANDLE DIALOG CLOSED")}
            onLogin={(username: string, password: string) => {
              console.log(`Username: ${username}, Password: ${password}`);
              setIsLoggedIn(true);
            }}
          />
        )}
      </Router>
    </StrictMode>
  );
}

createRoot(document.getElementById("root")!).render(<Root />);

import { StrictMode, useEffect, useState } from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import LoginDialog from "./components/LoginDialog.tsx";

function Root() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isBypassed, setIsByPassed] = useState(false);
  // const [loginAttempted, setLoginAttempted] = useState(false);
  // const [isAuthenticated, setIsAuthenticated] = useState(false);

  // const handleLogin = (username: string, password: string) => {
  //   console.log(`Username: ${username}, Password: ${password}`);

  //   /* ADD AUTH LOGIC HERE */
  //   /* Login was attempted but we dont know if they are authenticated yet */
  //   setLoginAttempted(true);
  //   const isAuthenticated = username !== "" && password !== "";
  // }

  /********************************************************************/
  /* HELLO MSG - check if api is responding */
  /********************************************************************/
  useEffect(() => {
    fetch("https://localhost:5004/hello")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTPS error: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Fetched data:", data);
      })
      .catch((error) => {
        console.error("Fetch error: ", error);
      });
  }, []); // slow to connect to the chat after every re-render, so you add the dependency array

  return (
    /********************************************************************/
    /* Determine first if user is logged in then display app */
    /********************************************************************/
    <StrictMode>
      <Router>
        {isLoggedIn || isBypassed ? (
          <App />
        ) : (
          <LoginDialog
            open={!isLoggedIn && !isBypassed}
            onClose={() => console.log("Login dialog closed")}
            onLoginSuccess={() => setIsLoggedIn(true)}
          />
        )}
      </Router>
    </StrictMode>
  );
}

createRoot(document.getElementById("root")!).render(<Root />);

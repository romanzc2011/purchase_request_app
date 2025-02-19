//import { useEffect } from "react";
import { StrictMode, useState } from "react";
import { BrowserRouter as Router } from "react-router-dom";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import LoginDialog from "./components/LoginDialog.tsx";

function Root() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  // Store user group perms
  const [ACCESS_GROUP, setACCESS_GROUP] = useState(false);
  const [CUE_GROUP, setCUE_GROUP] = useState(false);
  const [IT_GROUP, setIT_GROUP] = useState(false);

  const handleLoginSuccess = (access: boolean, cue: boolean, it: boolean) => {
    setIsLoggedIn(true);
    setACCESS_GROUP(access);
    setCUE_GROUP(cue);
    setIT_GROUP(it);
  };

  return (

    /********************************************************************/
    /* Determine first if user is logged in then display app */
    /********************************************************************/
    <StrictMode>
      <Router>
        {isLoggedIn ? (
          <App
            isLoggedIn={isLoggedIn}
            ACCESS_GROUP={ACCESS_GROUP}
            CUE_GROUP={CUE_GROUP}
            IT_GROUP={IT_GROUP}
          />
        ) : (
          <LoginDialog
            open={!isLoggedIn}
            onClose={() => console.log("Login dialog closed")}
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </Router>
    </StrictMode>
  );
}

createRoot(document.getElementById("root")!).render(<Root />);

//import { useEffect } from "react";
import { StrictMode, useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
    Navigate,
    Route,
    BrowserRouter as Router,
    Routes,
} from "react-router-dom";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import "./purchase_req/styles/index.css";
import App from "./purchase_req/views/App";
import LoginDialog from "./purchase_req/views/LoginDialog";
import ProtectedRoute from "./routes/ProtectedRoute";
import { prasStore } from "./store/prasStore";

const queryClient = new QueryClient();

function Root() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    // Store user group perms
    const [ACCESS_GROUP, setACCESS_GROUP] = useState(false);
    const [CUE_GROUP, setCUE_GROUP] = useState(false);
    const [IT_GROUP, setIT_GROUP] = useState(false);

    // Check for existing token on app startup
    useEffect(() => {
        const accessToken = localStorage.getItem("access_token");
        const userStr = localStorage.getItem("user");

        if (accessToken && userStr) {
            try {
                const user = JSON.parse(userStr);
                setIsLoggedIn(true);
                setACCESS_GROUP(user.ACCESS_GROUP || false);
                setCUE_GROUP(user.CUE_GROUP || false);
                setIT_GROUP(user.IT_GROUP || false);
            } catch (error) {
                console.error("Error parsing user data:", error);
                // Clear invalid data
                localStorage.removeItem("access_token");
                localStorage.removeItem("user");
            }
        }
    }, []);

    /* Using state management to 'dynamically' change which url to use, I'm finding it takes 
      significant configuration doing this manually, isOnSite refers to at LAWB office, had issues
      using localhost but Ethernet 3 IPv4 private addr always works */
    const handleLoginSuccess = (access: boolean, cue: boolean, it: boolean) => {
        setIsLoggedIn(true);
        setACCESS_GROUP(access);
        setCUE_GROUP(cue);
        setIT_GROUP(it);
    };

    return (
        <QueryClientProvider client={queryClient}>

            <StrictMode>
                <Router>
                    <Routes>
                        <Route path="/" element={<Navigate to="/purchase-request" />} />
                        {/*************************************************************/}
                        {/* LOGIN ROUTE */}
                        {/*************************************************************/}
                        <Route
                            path="/login"
                            element={
                                isLoggedIn ? (
                                    <Navigate to="/" replace />
                                ) : (
                                    <LoginDialog
                                        open={!isLoggedIn}
                                        onClose={() =>
                                            console.log("Login dialog closed.")
                                        }
                                        onLoginSuccess={handleLoginSuccess}
                                    />
                                )
                            }
                        />
                        {/*************************************************************/}
                        {/* PROTECTED ROUTES */}
                        {/*************************************************************/}
                        <Route
                            path="*"
                            element={
                                <ProtectedRoute isLoggedIn={isLoggedIn}>
                                    <Provider store={prasStore}>
                                        <App
                                            isLoggedIn={isLoggedIn}
                                            ACCESS_GROUP={ACCESS_GROUP}
                                            CUE_GROUP={CUE_GROUP}
                                            IT_GROUP={IT_GROUP}
                                        />
                                    </Provider>
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                </Router>
            </StrictMode>
        </QueryClientProvider>
    );
}

createRoot(document.getElementById("root")!).render(<Root />);

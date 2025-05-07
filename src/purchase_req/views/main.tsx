//import { useEffect } from "react";
import { StrictMode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
    Navigate,
    Route,
    BrowserRouter as Router,
    Routes,
} from "react-router-dom";
import { createRoot } from "react-dom/client";
import "./styles/index.css";
import App from "./App.tsx";
import LoginDialog from "./LoginDialog.tsx";
import ProtectedRoute from "../../routes/ProtectedRoute.tsx";

const queryClient = new QueryClient();

function Root() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    // Store user group perms
    const [ACCESS_GROUP, setACCESS_GROUP] = useState(false);
    const [CUE_GROUP, setCUE_GROUP] = useState(false);
    const [IT_GROUP, setIT_GROUP] = useState(false);

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
                                    <App
                                        isLoggedIn={isLoggedIn}
                                        ACCESS_GROUP={ACCESS_GROUP}
                                        CUE_GROUP={CUE_GROUP}
                                        IT_GROUP={IT_GROUP}
                                    />
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

import React, { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Routes, Route } from "react-router-dom";
import AddItemsForm from "./components/purchase_req/AddItemsForm";
import SubmitApprovalTable from "./components/purchase_req/SumbitToApproval";
import { Layout } from "./components/app_layout";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";
import ApprovalPageMain from "./components/approvals/ApprovalPageMain";
import { IFile } from "./types/IFile";
import LoginDialog from "./components/LoginDialog";

interface AppProps {
    isLoggedIn: boolean;
    ACCESS_GROUP: boolean;
    CUE_GROUP: boolean;
    IT_GROUP: boolean;
}

function App({ isLoggedIn, ACCESS_GROUP, CUE_GROUP, IT_GROUP }: AppProps) {
    /* *********************************************************************************** */
    /* SHARED DATA BUFFER */
    const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
    const [isSubmitted, setIsSubmitted] = useState(false); // Re-render once form is submitted
    const [fileInfo, setFileInfo] = useState<IFile[]>([]);
    const [loginOpen, setLoginOpen] = useState(!isLoggedIn);
    
    // Default ID for coms that need it
    const defaultId = `TEMP-${Date.now()}`;

    /* *********************************************************************************** */
    // Reset the Submit Table after submission
    const resetTable = () => {
        setDataBuffer([]);
    };

    const onDelete = (ID: string) => {
        setDataBuffer((prevData) =>
            prevData.filter((item) => item.ID !== ID)
        );
    };

    const handleLoginSuccess = (ACCESS_GROUP: boolean, CUE_GROUP: boolean, IT_GROUP: boolean) => {
        // Handle login success
        setLoginOpen(false);
    };

    /* *********************************************************************************** */
    // Update the title and icon of app
    useEffect(() => {
        document.title =
            "Puchase Request - Bankruptcy Court Wester District of Louisiana";
    }, []);

    /* *********************************************************************************** */
    /* Determine if ApprovalTable requires a login or not */
    let element;
    if (isLoggedIn) {
        element = (
            <ApprovalPageMain
                onDelete={onDelete}
                resetTable={resetTable}
            />
        );
    } else {
        element = (
            <LoginDialog
                open={loginOpen}
                onClose={() => setLoginOpen(false)}
                onLoginSuccess={handleLoginSuccess}
            />
        );
    }

    return (
        <Box sx={{ 
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            width: '100%'
        }}>
            {/* Sidebar Navigation */}
            {/* Layout component has the sidebar/header/main content */}
            <Layout
                ACCESS_GROUP={ACCESS_GROUP}
                CUE_GROUP={CUE_GROUP}
                IT_GROUP={IT_GROUP}
            >
                <Routes>
                    {/* Define Routes */}
                    {/* Password protect the routes, only authorized users can visit Approvals table */}
                    <Route path="/approvals" element={element} />;
                    <Route
                        path="/create-request"
                        element={
                            <>
                                {/********************************************************************* */}
                                {/* ADD ITEMS TO FORM - component */}
                                {/********************************************************************* */}
                                <AddItemsForm
                                    ID={defaultId}
                                    fileInfo={fileInfo}
                                    setDataBuffer={setDataBuffer}
                                    setIsSubmitted={setIsSubmitted}
                                    setFileInfo={setFileInfo}
                                />

                                {/********************************************************************* */}
                                {/* SUBMIT FORM TO APPROVAL TABLE - component */}
                                {/********************************************************************* */}
                                {/* isSubmitted and setIsSubmitted is what will determine to re-render the App or not, re-rendering is done
                    to get a new ID with each request */}
                                <Box
                                    className="col-md-12"
                                    style={{ marginTop: "20px" }}
                                >
                                    <SubmitApprovalTable
                                        ID={defaultId}
                                        dataBuffer={dataBuffer}
                                        onDelete={onDelete}
                                        fileInfo={fileInfo}
                                        isSubmitted={isSubmitted}
                                        setIsSubmitted={setIsSubmitted}
                                        setDataBuffer={setDataBuffer}
                                        setFileInfo={setFileInfo}
                                    />
                                </Box>
                            </>
                        }
                    />
                </Routes>
            </Layout>
        </Box>
    );
}

export default App;
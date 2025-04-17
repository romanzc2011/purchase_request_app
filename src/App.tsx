import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Routes, Route } from "react-router-dom";
import AddItemsForm from "./components/purchase_req/AddItemsForm";
import SubmitApprovalTable from "./components/purchase_req/SumbitToApproval";
import PurchaseSidenav from "./components/purchase_req/PurchaseSideBar";
import AlertMessage from "./components/AlertMessage";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";
import ApprovalPageMain from "./components/approvals/ApprovalPageMain";
import { IFile } from "./types/IFile";
const baseURL = import.meta.env.VITE_API_URL;

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
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [isSubmitted, setIsSubmitted] = useState(false); // Re-render once form is submitted
    const [fileInfo, setFileInfo] = useState<IFile[]>([]);
    
    // Default ID for coms that need it
    const defaultId = `TEMP-${Date.now()}`;

    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

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
                onDelete={(ID: number) =>
                    setDataBuffer(
                        dataBuffer.filter(
                            (item) => item.ID !== ID.toString()
                        )
                    )
                }
                resetTable={resetTable}
            />
        );
    } else {
        element = (
            <AlertMessage
                severity="error"
                alertText="Please log in to view this page."
            />
        );
    }

    return (
        <Box sx={{ display: "flex" }}>
            {/* Sidebar Navigation */}
            <PurchaseSidenav
                isOpen={sidebarOpen}
                toggleSidebar={toggleSidebar}
                ACCESS_GROUP={ACCESS_GROUP}
                CUE_GROUP={CUE_GROUP}
                IT_GROUP={IT_GROUP}
            />

            {/********************************************************************* */}
            {/* MAIN SECTION */}
            {/********************************************************************* */}
            <Box
                component={"main"}
                sx={{
                    padding: 3,
                    marginLeft: sidebarOpen ? "195px" : "60px", // Adjust dynamically
                    transition: "margin 0.3s ease", // Smooth transition
                }}
            >
                <Toolbar /> {/* Space to offset AppBar */}
                <Routes>
                    {/* Define Routes */}
                    {/* Password protect the routes, only authorized users can visit Approvals table */}
                    <Route path="/approvals-table" element={element} />;
                    <Route
                        path="/purchase-request"
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
            </Box>
        </Box>
    );
}

export default App;
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
import ApprovalsTable from "./components/approvals/ApprovalTable";
import { v4 as uuidv4 } from "uuid";
import { IFile } from "./types/IFile";

const drawerWidth = 195;

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
    const [finalSubmit, setFinalSubmit] = useState(false); // Clear out fileInfo once submitted
    const [fileInfo, setFileInfo] = useState<IFile[]>([]);

    // Setting reqID like this ensures a new reqID when the state changes and re-render occurs
    const [reqID, setReqID] = useState(() => uuidv4());

    // Function to toggle the sidebar
    const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

    /* *********************************************************************************** */
    // Reset the Submit Table after submission
    const resetTable = () => {
        setDataBuffer([]);
    };

    const onDelete = (reqID: string) => {
        setDataBuffer((prevData) =>
            prevData.filter((item) => item.reqID !== reqID)
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
            <ApprovalsTable
                //dataBuffer={dataBuffer}
                onDelete={(reqID: number) =>
                    setDataBuffer(
                        dataBuffer.filter(
                            (item) => item.reqID !== reqID.toString()
                        )
                    )
                }
                resetTable={resetTable}
                //setDataBuffer={setDataBuffer}
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
        <Box sx={{ display: "flex", height: "100vh" }}>
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
                    marginLeft: sidebarOpen ? `${drawerWidth}px` : "60px", // Adjust dynamically
                    transition: "margin 0.3s ease", // Smooth transition
                    overflow: "auto", // Enable scrolling if content overflows
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
                                    reqID={reqID}
                                    fileInfo={fileInfo}
                                    setDataBuffer={setDataBuffer}
                                    setIsSubmitted={setIsSubmitted}
                                    setReqID={setReqID}
                                    setFileInfo={setFileInfo}
                                />

                                {/********************************************************************* */}
                                {/* SUBMIT FORM TO APPROVAL TABLE - component */}
                                {/********************************************************************* */}
                                {/* isSubmitted and setIsSubmitted is what will determine to re-render the App or not, re-rendering is done
                    to get a new reqID with each request */}
                                <Box
                                    className="col-md-12"
                                    style={{ marginTop: "20px" }}
                                >
                                    <SubmitApprovalTable
                                        reqID={reqID}
                                        dataBuffer={dataBuffer}
                                        onDelete={onDelete}
                                        fileInfo={fileInfo}
                                        isSubmitted={isSubmitted}
                                        setIsSubmitted={setIsSubmitted}
                                        setReqID={setReqID}
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
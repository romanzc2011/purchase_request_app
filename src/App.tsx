import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import {
  Routes,
  Route,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { AddItemsForm } from "./components/purchase_req/AddItemsForm";
import SubmitApprovalTable from "./components/purchase_req/SubmitApprovalTable";
import PurchaseSidenav from "./components/purchase_req/PurchaseSideBar";
import LoginDialog from "./components/approvals/approvals_components/LoginDialog";
import AlertMessage from "./components/AlertMessage";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";
import ApprovalsTable from "./components/approvals/ApprovalTable";

const drawerWidth = 195;

function App() {
  /* *********************************************************************************** */
  /* SHARED DATA BUFFER */
  const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Function to toggle the sidebar
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  /* *********************************************************************************** */
  // Reset the Submit Table after submission
  const resetTable = () => {
    setDataBuffer([]);
  };

  /* *********************************************************************************** */
  // Update the title and icon of app
  useEffect(() => {
    document.title =
      "Puchase Request - Bankruptcy Court Wester District of Louisiana";
  }, []);

  /* *********************************************************************************** */
  /* Runs everytime dataBuffer changes */
  useEffect(() => {
    console.log("UPDATE dataBuffer: ", dataBuffer);
  }, [dataBuffer]);

  /* *********************************************************************************** */
  /* Get current route of user / redirect user to specified location */
  const location = useLocation();
  const navigate = useNavigate();

  return (
      <Box sx={{ display: "flex", height: "100vh" }}>
        {/* Sidebar Navigation */}
        <PurchaseSidenav isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />

        {/* *********************************************************************************** */}
        {/* Show login on /approvals-table if not logged in */}
        {location.pathname === "/approvals-table" && !isLoggedIn && (
          <LoginDialog
            open={!isLoggedIn} // Shows dialog if not logged in
            onClose={() => {
              // Redirecting to /purchase-request if not logged in and login dialog closed
              navigate("/purchase-request");
            }}
            onLogin={(username: string, password: string) => {
              console.log(`Username: ${username}, Password: ${password}`);
              setIsLoggedIn(true);
            }}
          />
        )}

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
            <Route
              path="/approvals-table"
              element={
                isLoggedIn ? (
                  <ApprovalsTable
                    dataBuffer={dataBuffer}
                    onDelete={(req_id: number) =>
                      setDataBuffer(
                        dataBuffer.filter((item) => item.req_id !== req_id)
                      )
                    }
                    resetTable={resetTable}
                  />
                ) : (
                  <AlertMessage
                    severity="error"
                    alertText="Please log in to view this page."
                  />
                )
              }
            />
            <Route
              path="/purchase-request"
              element={
                <>
                  <AddItemsForm
                    dataBuffer={dataBuffer}
                    setDataBuffer={setDataBuffer}
                  />
                  <Box className="col-md-12" style={{ marginTop: "20px" }}>
                    <SubmitApprovalTable
                      dataBuffer={dataBuffer}
                      onDelete={(req_id: number) =>
                        setDataBuffer(
                          dataBuffer.filter((item) => item.req_id !== req_id)
                        )
                      }
                      //resetTable={resetTable}
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

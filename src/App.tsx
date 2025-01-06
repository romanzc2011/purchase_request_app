import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { AddItemsForm } from "./components/purchase_req/purchase_req_components/AddItemsForm";
import SubmitApprovalTable from "./components/purchase_req/purchase_req_components/SubmitApprovalTable";
import PurchaseSidenav from "./components/purchase_req/purchase_req_components/PurchaseSideBar";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";
import ApprovalsTable from "./components/approvals/ApprovalTable";

const drawerWidth = 195;

function App() {
  /* *********************************************************************************** */
  /* SHARED DATA BUFFER */
  const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

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

  return (
    <Router>
      <Box sx={{ display: "flex", height: "100vh" }}>
        {/* Sidebar Navigation */}
        <PurchaseSidenav isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />

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
            <Route
              path="/approvals-table"
              element={
                <ApprovalsTable
                  dataBuffer={dataBuffer}
                  onDelete={(req_id: number) =>
                    setDataBuffer(
                      dataBuffer.filter((item) => item.req_id !== req_id)
                    )
                  }
                  resetTable={resetTable}
                />
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
                      resetTable={resetTable}
                    />
                  </Box>
                </>
              }
            />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

export default App;

import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { Routes, Route } from "react-router-dom";
import { AddItemsForm } from "./components/purchase_req/AddItemsForm";
import SubmitApprovalTable from "./components/purchase_req/SubmitApprovalTable";
import PurchaseSidenav from "./components/purchase_req/PurchaseSideBar";
import AlertMessage from "./components/AlertMessage";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";
import ApprovalsTable from "./components/approvals/ApprovalTable";
import { v4 as uuidv4 } from "uuid";

const drawerWidth = 195;

interface AppProps {
  isLoggedIn: boolean;
  ACCESS_GROUP: boolean;
  CUE_GROUP: boolean;
  IT_GROUP: boolean;
}

/* GENERATE REQ ID - pass this along to AddItems and FileUpload, unsure which one use will do first
    this ensures the req */
function generateReqID(): string {
  let myuuid = uuidv4();
  return myuuid;
}

function App({ isLoggedIn, ACCESS_GROUP, CUE_GROUP, IT_GROUP }: AppProps) {
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
  /* Determine if ApprovalTable requires a login or not */
  let element;
  if (isLoggedIn) {
    element = (
      <ApprovalsTable
        dataBuffer={dataBuffer}
        onDelete={(req_id: number) =>
          setDataBuffer(dataBuffer.filter((item) => item.req_id !== req_id.toString()))
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
                <AddItemsForm
                  dataBuffer={dataBuffer}
                  setDataBuffer={setDataBuffer}
                  requistionID={generateReqID()}
                />
                <Box className="col-md-12" style={{ marginTop: "20px" }}>
                  <SubmitApprovalTable
                    dataBuffer={dataBuffer}
                    onDelete={(req_id: string) =>
                      setDataBuffer(
                        dataBuffer.filter((item) => item.req_id !== req_id.toString())
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
import { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import { AddItemsForm } from "./components/AddItemsForm";
import SubmitApprovalTable from "./components/SubmitApprovalTable";
import PurchaseSidenav from "./components/PurchaseSideBar";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "./types/formTypes";

function App() {

  /* *********************************************************************************** */
  /* SHARED DATA BUFFER */
  const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);

  // Reset the Submit Table after submission
  const resetTable = () => {
    setDataBuffer([]);
  }

  // Update the title and icon of app
  useEffect(() => {
    document.title =
      "Puchase Request - Bankruptcy Court Wester District of Louisiana";
  });

  /* Runs everytime dataBuffer changes */
  useEffect(() => {
    console.log("UPDATE dataBuffer: ", dataBuffer);
  }, [dataBuffer]);

  return (
    <Box>
      <PurchaseSidenav />

      {/********************************************************************* */}
      {/* MAIN SECTION */}
      {/********************************************************************* */}
      <Box component={"main"} sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* Space to offset AppBar */}
        {/* Add Items Form */}
        <AddItemsForm dataBuffer={dataBuffer} setDataBuffer={setDataBuffer} />
        
        {/********************************************************************* */}
        {/* TABLE SECTION --- where items will be reviewed and submitted for
             approval*/}
        {/********************************************************************* */}
        <Box className="col-md-12" style={{ marginTop: "20px" }}>
          <SubmitApprovalTable
            dataBuffer={dataBuffer}
            onDelete={(id: number) =>
              setDataBuffer(dataBuffer.filter((item) => item.id !== id))
            }
            resetTable={resetTable}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default App;

import { useEffect, useState } from "react";
import PurchasePicker from "./components/SubmitApprovalForm";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import PurchaseForm from "./components/AddItemsForm";
import PurchaseSidenav from "./components/PurchaseSideBar";
import { Box, Toolbar } from "@mui/material";

function App() {
  // Update the title and icon of app
  useEffect(() => {
    document.title =
      "Puchase Request - Bankruptcy Court Wester District of Louisiana";
  });
  const [currentTime, setCurrentTime] = useState(0);

  /* React example of send a request to python backend */
  useEffect(() => {
    fetch("http://127.0.0.1:5000/time")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("Fetched time:", data.time);
        setCurrentTime(data.time);
      })
      .catch((err) => console.error("Error fetching time:", err));
  }, []);

  /* TEST DATA *********************************************************** */
  const [purchases, setPurchases] = useState([
    {
      BOC: 1,
      fund: "aaa",
      location: "Shreveport, LA",
      description: "Utilities",
      quantity: 3,
      price: 10,
      estimatedCost: 100,
      justification: "need",
    },
  ]);

  return (
    <div>
      <PurchaseSidenav />

      {/* MAIN SECTION */}
      <Box component={"main"} sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* Space to offset AppBar */}
        {/* Form Section */}
        <PurchaseForm />
        <div className="col-md-12" style={{ marginTop: "20px" }}>
          <PurchasePicker
            purchases={purchases}
            onDelete={(id) =>
              setPurchases(purchases.filter((e) => e.BOC !== id))
            }
          />
        </div>
      </Box>
      {/********************************************************************* */}
      {/* FORM SECTION */}
      {/********************************************************************* */}
    </div>
  );
}

export default App;

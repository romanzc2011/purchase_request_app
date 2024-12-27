import { useEffect, useState } from "react";
import PurchasePicker from "./components/PurchasePicker";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import PurchaseForm from "./components/PurchaseForm";
import PickerFilter from "./components/PickerFilter";
import FundFilter from "./components/FundFilter";
import LocationFilter from "./components/LocationFilter";

function App() {
  const [currentTime, setCurrentTime] = useState(0);

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

  // Update the title and icon of app
  useEffect(() => {
    document.title =
      "Puchase Request Form - Bankruptcy Court Wester District of Louisiana";
  });

  return (
    <div className="container-fluid">
      <p>Current time {currentTime}.</p>
      {/********************************************************************* */}
      {/* FORM SECTION */}
      {/********************************************************************* */}
      {/* Layout for Form and Table */}
      <div className="row d-flex">
        {/* Form Section */}
        <div className="col-md-12">
          <PurchaseForm />
        </div>

        {/********************************************************************* */}
        {/* PURCHASE PICKER */}
        {/********************************************************************* */}

        {/* BUDGET OBJECT CODE */}
        <div className="row col-sm-12 mb-3">
          <label htmlFor="budgetObjCode" className="col-sm-3 col-form-label">
            <strong>Budget Object Code (BOC)</strong>
          </label>
          <div className="col-sm-8 d-flex" style={{ paddingRight: "71px"}}>
            <PickerFilter
              onSelectCategory={(category) => console.log(category)}
            />

            {/* FUND */}
            <label htmlFor="fund" className="col-sm-2 col-form-label">
              <strong>Fund</strong>
            </label>
            <div className="col-sm-2">
              <FundFilter onSelectFund={(fund) => console.log(fund)} />
            </div>
          </div>
        </div>

        {/* LOCATION */}
        <div className="row col-sm-12">
        <label htmlFor="location" className="col-sm-2 col-form-label" style={{ paddingLeft: "80px"}}>
              <strong>Location</strong>
            </label>
            <div className="col-sm-6" style={{ paddingLeft: "110px"}} >
              <LocationFilter onSelectLocation={(location) => console.log(location)} />
            </div>
          </div>
        </div>
        <div className="col-md-12" style={{ marginTop: "20px" }}>
          <PurchasePicker
            purchases={purchases}
            onDelete={(id) =>
              setPurchases(purchases.filter((e) => e.BOC !== id))
            }
          />
        </div>
      </div>
  );
}

export default App;

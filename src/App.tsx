import { useEffect, useState } from "react";
import PurchaseList from "./components/PurchaseList";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import PurchaseForm from "./components/PurchaseForm";

function App() {
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
    document.title = "Puchase Request Form - Bankruptcy Court Wester District of Louisiana";
  });

  return (
    <div className="container-fluid">

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
        {/* Table Section */}
        {/********************************************************************* */}
        <div className="col-md-12" style={{ marginTop: '20px'}}>
          <PurchaseList
            purchases={purchases}
            onDelete={(id) =>
              setPurchases(purchases.filter((e) => e.BOC !== id))
            }
          />
        </div>
      </div>
    </div>
  );
}

export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import PurchaseRequestForm from './components/purchase_req/PurchaseRequestForm';
import RequestsWaiting from './components/requests/RequestsWaiting';

const App = () => {
    return (
      <Router>
        <nav>
          <Link to="/purchase-request">New Request</Link>
          <Link to="/requests-table">Requests Table</Link>
        </nav>
        <Routes>
          <Route path="/purchase-request" element={<PurchaseRequestForm />} />
          <Route path="/requests-table" element={<RequestsWaiting />} />
        </Routes>
      </Router>
    );
  };
  
  export default App;
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Default route to Dashboard */}
        <Route path="/" element={<Dashboard />} />
        {/* Add more routes as needed */}
      </Routes>
    </Router>
  );
};

export default App;

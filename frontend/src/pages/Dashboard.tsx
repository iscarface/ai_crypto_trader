import React from "react";
import TradeHistory from "../components/TradeHistory";
import PerformanceChart from "../components/PerformanceChart";

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1>Trading Dashboard</h1>
      <PerformanceChart />
      <TradeHistory />
    </div>
  );
};

export default Dashboard;

import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PerformanceData {
  timestamp: string;
  portfolio_value: number;
  profit_loss: number;
}

const PerformanceChart: React.FC = () => {
  const [data, setData] = useState<PerformanceData[]>([]);

  useEffect(() => {
    axios
      .get<PerformanceData[]>("/api/performance")
      .then((response) => setData(response.data))
      .catch((error) => console.error("Error fetching performance data:", error));
  }, []);

  return (
    <div>
      <h2>Portfolio Performance</h2>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" tickFormatter={(time) => new Date(time).toLocaleTimeString()} />
          <YAxis />
          <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
          <Line type="monotone" dataKey="portfolio_value" stroke="#8884d8" name="Portfolio Value" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceChart;

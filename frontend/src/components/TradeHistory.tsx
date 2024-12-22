import React, { useEffect, useState } from "react";
import axios from "axios";

interface Trade {
  id: number;
  symbol: string;
  action: string; // BUY or SELL
  price: number;
  entry_price?: number | null; // Optional
  exit_price?: number | null;  // Optional
  quantity: number;
  profit_loss: number | null;  // Allow null but not undefined
  timestamp: string;
  status: string;
}


const TradeHistory: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    axios
      .get<Trade[]>("/api/trades")
      .then((response) => {
        console.log("Fetched trades:", response.data); // Debugging line
        setTrades(response.data);
      })
      .catch((error) => {
        console.error("Error fetching trade history:", error);
      });
  }, []);

  return (
    <div>
      <h2>Trade History</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Status</th>
            <th>Entry Price</th>
            <th>Exit Price</th>
            <th>Profit/Loss</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id}>
              <td>{trade.symbol || "N/A"}</td>
              <td>{trade.status}</td>
              <td>${trade.entry_price}</td>
              <td>{trade.exit_price !== undefined && trade.exit_price !== null ? "$" + trade.exit_price.toFixed(4) : "--"}</td>
              <td
                style={{
                  color: trade.profit_loss !== undefined && trade.profit_loss !== null && trade.profit_loss >= 0 ? "green" : "red",
                }}
              >
                {trade.profit_loss !== undefined && trade.profit_loss !== null
                  ? `${trade.profit_loss.toFixed(2)}%`
                  : "--"}
              </td>
              <td>
                {trade.timestamp
                  ? new Date(trade.timestamp).toLocaleString()
                  : "Invalid Date"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TradeHistory;

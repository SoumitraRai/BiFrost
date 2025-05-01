import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [logs, setLogs] = useState("");
  const [pendingPayments, setPendingPayments] = useState<
    { id: number; message: string }[]
  >([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch("/proxy_logs/proxy.log");
        const data = await response.text();
        setLogs(data);
      } catch (error) {
        console.error("Error fetching logs:", error);
        setLogs("Error fetching logs from server.");
      }
    };

    const fetchPaymentRequests = async () => {
      try {
        const response = await fetch("/proxy_logs/payment_links.txt");
        const text = await response.text();
        const lines = text.split("\n").filter(Boolean);

        const formattedRequests = lines.map((url, index) => ({
          id: index + 1,
          message: `Payment request from url - ${url}`,
        }));

        setPendingPayments(formattedRequests);
      } catch (error) {
        console.error("Error loading payment requests:", error);
      }
    };

    fetchLogs();
    fetchPaymentRequests();

    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = (id: number) => {
    console.log(`Approved payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
    // Optional: Send approval to backend
  };

  const handleDeny = (id: number) => {
    console.log(`Denied payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
    // Optional: Send denial to backend
  };

  return (
    <div>
      <h1 className="main-heading">Bifrost</h1>
      <p className="tagline">Parental Payment Guardian System</p>

      <div className="box-wrapper">
        <div className="container-box">
          <h2>Pending Approvals</h2>
          <ul className="pending-list">
            {pendingPayments.map((item) => (
              <li key={item.id} className="pending-item">
                <span>{item.message}</span>
                <div className="button-group">
                  <button onClick={() => handleApprove(item.id)}>Approve</button>
                  <button onClick={() => handleDeny(item.id)}>Deny</button>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="container-box">
          <h2>Traffic Logs</h2>
          <textarea
            readOnly
            className="traffic-log-box"
            value={logs}
          />
        </div>
      </div>
    </div>
  );
}

export default App;

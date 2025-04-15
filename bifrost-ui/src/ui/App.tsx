import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [logs, setLogs] = useState("");
  const [pendingPayments, setPendingPayments] = useState([
    { id: 1, message: "Payment request from url - https://paytm.com/recharge-bill-payment" },
    { id: 2, message: "Payment request from url - https://paytm.com/recharge-bill-payment" },
    { id: 3, message: "Payment request from url - https://paytm.com/recharge-bill-payment" },
    { id: 4, message: "Payment request from url - https://paytm.com/recharge-bill-payment" },
    { id: 5, message: "Payment request from url - https://paytm.com/recharge-bill-payment" },
  ]);

  useEffect(() => {
    // Replace with your real proxy server endpoint
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

    fetchLogs();

    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = (id) => {
    console.log(`Approved payment ID: ${id}`);
    setPendingPayments(pendingPayments.filter(item => item.id !== id));
    // You can send approval to backend here
  };

  const handleDeny = (id) => {
    console.log(`Denied payment ID: ${id}`);
    setPendingPayments(pendingPayments.filter(item => item.id !== id));
    // You can send denial to backend here
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

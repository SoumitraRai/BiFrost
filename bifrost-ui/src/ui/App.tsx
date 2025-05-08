import React, { useState, useEffect } from "react";
import "./App.css";
import Login from "./login";
import Register from "./register";

function App() {
  const [logs, setLogs] = useState("");
  const [pendingPayments, setPendingPayments] = useState<{ id: number; message: string }[]>([]);
  const [page, setPage] = useState<'start' | 'login' | 'register' | 'app'>('start');
  const [role, setRole] = useState<string>("");

  useEffect(() => {
    if (role !== "Admin") return;

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
        const response = await fetch("/proxy_logs/payment_traffic.log");
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
    const interval = setInterval(() => {
      fetchLogs();
      fetchPaymentRequests();
    }, 100);

    return () => clearInterval(interval);
  }, [role]);

  const handleApprove = (id: number) => {
    console.log(`Approved payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
  };

  const handleDeny = (id: number) => {
    console.log(`Denied payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
  };

  // Start Page
  if (page === 'start') {
    return (
      <div className="start-page">
        <h1>Welcome to Bifrost</h1>
        <p className="tagline">Parental Payment Guardian System</p>
        <button onClick={() => setPage('login')} className="btn">Login</button>
        <button onClick={() => setPage('register')} className="btn">Register</button>
      </div>
    );
  }

  // Login Page
  if (page === 'login') {
    return (
      <Login 
        onLogin={(r) => { setRole(r); setPage('app'); }}
        onBack={() => setPage('start')}
      />
    );
  }

  // Register Page
  if (page === 'register') {
    return (
      <Register 
        onRegistered={() => setPage('login')}
        onBack={() => setPage('start')}
      />
    );
  }

  // Client View
  if (page === 'app' && role === "Client") {
    return (
      <div className="client-view">
        <h1>Hi, Client</h1>
        <button onClick={() => { setRole(""); setPage("start"); }} className="btn">Logout</button>
      </div>
    );
  }

  // Admin View
  return (
    <div>
      <h1 className="main-heading">Bifrost</h1>
      <p className="tagline">Parental Payment Guardian System</p>
      <button onClick={() => { setRole(""); setPage("start"); }} className="btn logout-btn">Logout</button>

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
          <textarea readOnly className="traffic-log-box" value={logs} />
        </div>
      </div>
    </div>
  );
}

export default App;
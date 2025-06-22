import React, { useState, useEffect } from "react";
import "../styles/Admin.css";

type PendingPayment = {
  id: number;
  message: string;
};

type AdminProps = {
  logs: string;
  onLogout: () => void;
};

const Admin: React.FC<AdminProps> = ({
  logs,
  onLogout,
}) => {
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([]);

  useEffect(() => {
    const fetchPaymentRequests = async () => {
      try {
        const response = await fetch("/proxy_logs/payment_traffic.log");
        const text = await response.text();
        const lines = text.split("\n").filter(Boolean);
        const formattedRequests = lines.map((url, index) => ({
          id: index + 1,
          message: `${url}`,
        }));
        setPendingPayments(formattedRequests);
      } catch (error) {
        console.error("Error loading payment requests:", error);
      }
    };

    fetchPaymentRequests();
    const interval = setInterval(fetchPaymentRequests, 100);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = (id: number) => {
    console.log(`Approved payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
  };

  const handleDeny = (id: number) => {
    console.log(`Denied payment ID: ${id}`);
    setPendingPayments((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <div>
      <div className="header-bar">
        <div>
          <h1 className="main-heading">Bifrost</h1>
          <p className="tagline">Parental Payment Guardian</p>
        </div>
        <button onClick={onLogout} className="btn logout-btn">Logout</button>
      </div>

      <div className="box-wrapper">
        <div className="container-box">
          <h2>Pending Approvals</h2>
          <ul className="pending-list">
            {pendingPayments.map((item) => (
              <li key={item.id} className="pending-item">
                <span>{item.message}</span>
                <div className="button-group">
                  <button onClick={() => handleApprove(item.id)}>✔</button>
                  <button onClick={() => handleDeny(item.id)}>✘</button>
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
};

export default Admin;
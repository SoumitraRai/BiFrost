import React, { useState, useEffect } from "react";
import "../styles/Client.css";

type ClientProps = {
  onLogout: () => void;
};

const Client: React.FC<ClientProps> = ({ onLogout }) => {
  const [pendingRequests, setPendingRequests] = useState([
    { id: 1, message: "Payment Request to Amazon.com - $29.99", status: "Pending" },
    { id: 2, message: "Payment Request to Netflix.com - $15.99", status: "Pending" },
    { id: 3, message: "Payment Request to Steam Store - $59.99", status: "Pending" },
  ]);

  return (
    <div className="client-page">
      <div className="header-bar">
        <div>
          <h1 className="main-heading">Bifrost</h1>
          <p className="tagline">Parental Payment Guardian</p>
        </div>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>

      <div className="client-wrapper">
        <div className="container-box-client">
          <h2>Payment Requests</h2>
          <div className="requests-container">
            {pendingRequests.length === 0 ? (
              <div className="no-requests">
                <p>No pending requests</p>
              </div>
            ) : (
              <div className="requests-scroll-box">
                <ul className="request-list">
                  {pendingRequests.map((request) => (
                    <li key={request.id} className="request-item">
                      <div className="request-content">
                        <span className="request-message">{request.message}</span>
                        <div className="request-status">
                          <span className={`status-badge ${request.status.toLowerCase()}`}>
                            {request.status === "Pending" && "⏳ Sending Request to Admin for Approval..."}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      <footer className="client-footer">
        <p>Copyright &copy; Team Bifrost</p>
      </footer>
    </div>
  );
};

export default Client;
import React from "react";

type ClientProps = {
  onLogout: () => void;
};

const Client: React.FC<ClientProps> = ({ onLogout }) => (
  <div className="client-view">
    <h1>Hi, Client</h1>
    <button onClick={onLogout} className="btn">Logout</button>
  </div>
);

export default Client;
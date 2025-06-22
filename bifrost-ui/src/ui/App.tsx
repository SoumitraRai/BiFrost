import React, { useState, useEffect } from "react";
import "./styles/App.css";
import Login from "./components/login";
import Register from "./components/register";
import Start from "./components/start"; 
import Client from "./components/Client";
import Admin from "./components/Admin";

function App() {
  const [logs, setLogs] = useState("");
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

    fetchLogs();
    const interval = setInterval(fetchLogs, 100);

    return () => clearInterval(interval);
  }, [role]);

  // Start Page
  if (page === 'start') {
    return (
      <Start
        onLogin={() => setPage('login')}
        onRegister={() => setPage('register')}
      />
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
      <Client onLogout={() => { setRole(""); setPage("start"); }} />
    );
  }

  // Admin View
  return (
    <Admin
      logs={logs}
      onLogout={() => { setRole(""); setPage("start"); }}
    />
  );
}

export default App;
import React from "react";
import "../styles/start.css";

interface StartProps {
  onLogin: () => void;
  onRegister: () => void;
}

const Start: React.FC<StartProps> = ({ onLogin, onRegister }) => (
  <div className="start-page">
    <h1 className="headline-gradient">Welcome to Bifrost</h1>
    <p className="tagline-glow">Parental Payment Guardian System</p>
    <p className="subtitle-fancy">Secure. Smart. In Control.</p>
    <button onClick={onLogin} className="btn">Login</button>
    <button onClick={onRegister} className="btn">Register</button>
  </div>
);

export default Start;
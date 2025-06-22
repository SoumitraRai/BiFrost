import React, { useState } from "react";
import "../styles/login.css";

type Props = {
    onLogin: (role: string) => void;
    onBack: () => void;
};

export default function Login({ onLogin, onBack }: Props) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleLogin = async () => {
        const trimmedUsername = username.trim();
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: trimmedUsername, password }),
            });
            const data = await response.json();
            if (!response.ok) {
                setError(data.message || "Invalid username or password.");
                return;
            }
            setError("");
            onLogin(data.role);
        } catch (err) {
            setError("Error connecting to server.");
        }
    };

    return (
        <div className="auth-center">
            <div className="auth-container">
                <h2>Login</h2>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="auth-input"
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="auth-input"
                />
                <div className="button-group">
                    <button onClick={handleLogin} className="auth-button">Login</button>
                    <button onClick={onBack} className="auth-button">Back</button>
                </div>
                {error && <p className="error-message">{error}</p>}
            </div>
        </div>
    );
}
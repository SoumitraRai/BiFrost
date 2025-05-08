import React, { useState } from "react";

type Props = {
    onLogin: (role: string) => void;
    onBack: () => void;
};

export default function Login({ onLogin, onBack }: Props) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleLogin = () => {
        const trimmedUsername = username.trim();
        const users = JSON.parse(localStorage.getItem("users") || "[]");

        const user = users.find(
            (u: any) => u.username === trimmedUsername && u.password === password
        );

        if (user) {
            setError("");
            onLogin(user.role);
        } else {
            setError("Invalid username or password.");
        }
    };

    return (
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
    );
}
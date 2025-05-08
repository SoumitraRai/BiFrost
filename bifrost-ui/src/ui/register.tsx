import React, { useState } from "react";

type Props = {
    onRegistered: () => void;
    onBack: () => void;
};

export default function Register({ onRegistered, onBack }: Props) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<'Admin' | 'Client'>('Client');

    const handleRegister = () => {
        const users = JSON.parse(localStorage.getItem("users") || "[]");
        if (users.find((u: any) => u.username === username)) {
            alert("Username already exists.");
            return;
        }
        users.push({ username, password, role });
        localStorage.setItem("users", JSON.stringify(users));
        alert("Registered successfully.");
        onRegistered();
    };

    return (
        <div className="auth-container">
            <h2>Register</h2>
            <input 
                placeholder="Username" 
                onChange={(e) => setUsername(e.target.value)}
                className="auth-input"
            />
            <input 
                type="password" 
                placeholder="Password" 
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
            />
            <select 
                onChange={(e) => setRole(e.target.value as 'Admin' | 'Client')}
                className="auth-input"
            >
                <option value="Client">Client</option>
                <option value="Admin">Admin</option>
            </select>
            <div className="button-group">
                <button onClick={handleRegister} className="auth-button">Register</button>
                <button onClick={onBack} className="auth-button">Back</button>
            </div>
        </div>
    );
}
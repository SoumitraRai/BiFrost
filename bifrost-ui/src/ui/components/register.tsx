import React, { useState } from "react";
import "../styles/login.css";

type Props = {
    onRegistered: () => void;
    onBack: () => void;
};

export default function Register({ onRegistered, onBack }: Props) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<'Admin' | 'Client'>('Client');

    const handleRegister = async () => {
        try {
            const response = await fetch('/api/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password, role }),
});
            const data = await response.json();
            if (!response.ok) {
                alert(data.message || "Registration failed.");
                return;
            }
            alert("Registered successfully.");
            onRegistered();
        } catch (error) {
            alert("An error occurred. Please try again.");
        }
    };

    return (
        <div className='auth-center'>
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
        </div>
    );
}
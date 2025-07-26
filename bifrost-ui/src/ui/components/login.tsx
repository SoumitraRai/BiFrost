import React, { useState } from "react";
import "../styles/login.css";

// Define the API interface for TypeScript
declare global {
  interface Window {
    api?: {
      send: (channel: string, data: unknown) => void;
      receive: (channel: string, func: (...args: unknown[]) => void) => number;
      removeListener: (channel: string, listenerId: number) => boolean;
      invoke: (channel: string, data?: unknown) => Promise<unknown>;
      cleanup: (channel: string) => void; // Legacy method
      invokeLogin?: (userData: {username: string, password: string}) => Promise<{success: boolean, message: string, role?: string}>;
    };
  }
}

type Props = {
    onLogin: (role: string) => void;
    onBack: () => void;
};

export default function Login({ onLogin, onBack }: Props) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoggingIn, setIsLoggingIn] = useState(false);

    const handleLogin = async () => {
        const trimmedUsername = username.trim();
        if (!trimmedUsername || !password) {
            setError("Username and password are required.");
            return;
        }
        
        setError("");
        setIsLoggingIn(true);
        
        try {
            // First, try direct HTTP request
            console.log("Sending login request");
            
            // Use AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            try {
                const response = await fetch('http://localhost:3001/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: trimmedUsername, password }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                let data;
                try {
                    const text = await response.text();
                    console.log("Raw response:", text);
                    data = JSON.parse(text);
                } catch (parseError) {
                    console.error("Failed to parse response:", parseError);
                    setIsLoggingIn(false);
                    setError("Invalid response from server.");
                    return;
                }
                
                console.log("Login response:", data);
                
                setIsLoggingIn(false);
                
                if (!response.ok) {
                    setError(data.message || "Login failed.");
                    return;
                }
                
                setError("");
                onLogin(data.role);
                
            } catch (fetchError: any) {
                clearTimeout(timeoutId);
                console.error("Fetch error:", fetchError);
                
                // If direct fetch fails and we're in Electron, try the IPC method
                if (window.api && window.api.invokeLogin) {
                    console.log("Direct HTTP failed. Falling back to invokeLogin method");
                    
                    try {
                        const result = await window.api.invokeLogin({ 
                            username: trimmedUsername, 
                            password 
                        });
                        
                        console.log("Login result:", result);
                        
                        setIsLoggingIn(false);
                        
                        if (result.success && result.role) {
                            setError("");
                            onLogin(result.role);
                        } else {
                            setError(result.message || "Login failed.");
                        }
                    } catch (error) {
                        console.error("IPC login error:", error);
                        setIsLoggingIn(false);
                        setError("Login failed. Please check your connection and try again.");
                    }
                } else {
                    setIsLoggingIn(false);
                    
                    if (fetchError.name === 'AbortError') {
                        setError("Request timed out. Please try again.");
                    } else {
                        setError("Network error. Please check your connection.");
                    }
                }
            }
        } catch (error) {
            console.error("Unexpected login error:", error);
            setIsLoggingIn(false);
            setError("An unexpected error occurred. Please try again.");
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
                    <button 
                        onClick={handleLogin} 
                        className="auth-button"
                        disabled={isLoggingIn}
                    >
                        {isLoggingIn ? 'Logging in...' : 'Login'}
                    </button>
                    <button 
                        onClick={onBack} 
                        className="auth-button"
                        disabled={isLoggingIn}
                    >
                        Back
                    </button>
                </div>
                {error && <p className="error-message">{error}</p>}
            </div>
        </div>
    );
}
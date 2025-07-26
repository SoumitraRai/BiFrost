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
      // Add a new invokeRegister method for a completely different approach
      invokeRegister?: (userData: {username: string, password: string, role: string}) => Promise<{success: boolean, message: string}>;
    };
    // Add timeout ID for registration requests
    registrationTimeoutId?: number | ReturnType<typeof setTimeout>;
  }
}

type Props = {
    onRegistered: () => void;
    onBack: () => void;
};

export default function Register({ onRegistered, onBack }: Props) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<'Admin' | 'Client'>('Client');
    const [isRegistering, setIsRegistering] = useState(false);

    // We're removing the useEffect and listener approach completely
    // No more listeners = no more GLib-GObject errors!

    const handleRegister = async () => {
        if (!username || !password) {
            alert("Please enter a username and password.");
            return;
        }
        
        // Add more validation
        if (username.length < 3) {
            alert("Username must be at least 3 characters.");
            return;
        }
        
        if (password.length < 6) {
            alert("Password must be at least 6 characters.");
            return;
        }

        setIsRegistering(true);
        
        try {
            // First, try direct HTTP request to avoid IPC complexity
        console.log("Sending registration request");
        
        try {
            // Always try the direct fetch approach first for simplicity
            console.log("Using direct HTTP request");
            
            // Use AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            try {
                const response = await fetch('http://localhost:3001/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, role }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                let data;
                try {
                    data = await response.json();
                } catch (parseError) {
                    console.error("Failed to parse response:", parseError);
                    setIsRegistering(false);
                    alert("Invalid response from server.");
                    return;
                }
                
                console.log("Registration response:", data);
                
                setIsRegistering(false);
                
                if (!response.ok) {
                    alert(data.message || "Registration failed.");
                    return;
                }
                
                alert("Registered successfully!");
                onRegistered();
                
            } catch (fetchError: any) {
                clearTimeout(timeoutId);
                console.error("Fetch error:", fetchError);
                
                // If direct fetch fails and we're in Electron, try the IPC method
                if (window.api && window.api.invokeRegister) {
                    console.log("Direct HTTP failed. Falling back to invokeRegister method");
                    
                    try {
                        const result = await window.api.invokeRegister({ 
                            username, 
                            password, 
                            role 
                        });
                        
                        console.log("Registration result:", result);
                        
                        setIsRegistering(false);
                        
                        if (result.success) {
                            alert("Registered successfully!");
                            onRegistered();
                        } else {
                            alert(result.message || "Registration failed.");
                        }
                    } catch (error) {
                        console.error("IPC registration error:", error);
                        setIsRegistering(false);
                        alert("Registration failed. Please check your connection and try again.");
                    }
                } else {
                    setIsRegistering(false);
                    
                    if (fetchError.name === 'AbortError') {
                        alert("Request timed out. Please try again.");
                    } else {
                        alert("Network error. Please check your connection.");
                    }
                }
            }
        } catch (error) {
            console.error("Unexpected registration error:", error);
            setIsRegistering(false);
            alert("An unexpected error occurred. Please try again.");
        }
        } catch (error) {
            console.error("Unexpected registration error:", error);
            setIsRegistering(false);
            alert("An unexpected error occurred. Please try again.");
        }
    };

    return (
        <div className='auth-center'>
            <div className="auth-container">
                <h2>Register</h2>
                <input 
                    placeholder="Username" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="auth-input"
                    disabled={isRegistering}
                />
                <input 
                    type="password" 
                    placeholder="Password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="auth-input"
                    disabled={isRegistering}
                />
                <select 
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'Admin' | 'Client')}
                    className="auth-input"
                    disabled={isRegistering}
                >
                    <option value="Client">Client</option>
                    <option value="Admin">Admin</option>
                </select>
                <div className="button-group">
                    <button 
                        onClick={handleRegister} 
                        className="auth-button"
                        disabled={isRegistering}
                    >
                        {isRegistering ? 'Registering...' : 'Register'}
                    </button>
                    <button 
                        onClick={onBack} 
                        className="auth-button"
                        disabled={isRegistering}
                    >
                        Back
                    </button>
                </div>
            </div>
        </div>
    );
}
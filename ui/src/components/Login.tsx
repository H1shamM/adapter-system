import {useState} from "react";
import {login} from "../api/auth.ts";
import {setToken} from "../api/token.ts";

export default function Login({onLogin}: {onLogin: () => void}) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    async function handleLogin() {
        try {
            const data = await login(username, password);
            setToken("access",data.access_token)
            setToken("refresh", data.refresh_token)
            onLogin();
        }
        catch {
            alert("Failed to login");
        }
    }

    return (
        <div>
            <h2>Admin Login</h2>
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
            <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleLogin}>Login</button>
        </div>
    );
}
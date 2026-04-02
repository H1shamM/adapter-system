import {useState} from "react";
import {login} from "../api/auth.ts";
import {setToken} from "../api/token.ts";

export default function Login({onLogin}: {onLogin: () => void}) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleLogin() {
        setError("");
        setLoading(true);
        try {
            const data = await login(username, password);
            setToken("access", data.access_token)
            setToken("refresh", data.refresh_token)
            onLogin();
        } catch {
            setError("Invalid credentials. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    function handleKeyDown(e: React.KeyboardEvent) {
        if (e.key === 'Enter') handleLogin();
    }

    return (
        <div style={styles.wrapper}>
            <div style={styles.card}>
                <div style={styles.logoArea}>
                    <div style={styles.logoIcon}>⚡</div>
                    <h2 style={styles.title}>Adapter System</h2>
                    <p style={styles.subtitle}>Sign in to your dashboard</p>
                </div>

                {error && <div style={styles.error}>{error}</div>}

                <div style={styles.field}>
                    <label style={styles.label}>Username</label>
                    <input
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Enter username"
                        style={styles.input}
                    />
                </div>

                <div style={styles.field}>
                    <label style={styles.label}>Password</label>
                    <input
                        value={password}
                        type="password"
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Enter password"
                        style={styles.input}
                    />
                </div>

                <button
                    onClick={handleLogin}
                    disabled={loading || !username || !password}
                    style={{
                        ...styles.button,
                        opacity: (loading || !username || !password) ? 0.6 : 1,
                    }}
                >
                    {loading ? 'Signing in...' : 'Sign In'}
                </button>
            </div>
        </div>
    );
}

const styles = {
    wrapper: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#f5f6fa',
    },
    card: {
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '40px',
        width: '100%',
        maxWidth: '400px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
    },
    logoArea: {
        textAlign: 'center' as const,
        marginBottom: '32px',
    },
    logoIcon: {
        fontSize: '40px',
        marginBottom: '12px',
    },
    title: {
        margin: '0 0 4px 0',
        fontSize: '24px',
        fontWeight: 700,
        color: '#1f2937',
    },
    subtitle: {
        margin: 0,
        fontSize: '14px',
        color: '#6b7280',
    },
    error: {
        padding: '10px 14px',
        marginBottom: '16px',
        backgroundColor: '#fef2f2',
        color: '#991b1b',
        borderRadius: '8px',
        fontSize: '13px',
        border: '1px solid #fecaca',
    },
    field: {
        marginBottom: '16px',
    },
    label: {
        display: 'block',
        fontSize: '13px',
        fontWeight: 600,
        color: '#374151',
        marginBottom: '6px',
    },
    input: {
        width: '100%',
        padding: '10px 14px',
        fontSize: '14px',
        border: '1px solid #d1d5db',
        borderRadius: '8px',
        outline: 'none',
        transition: 'border-color 0.15s',
        boxSizing: 'border-box' as const,
    },
    button: {
        width: '100%',
        padding: '12px',
        fontSize: '15px',
        fontWeight: 600,
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        marginTop: '8px',
    } as React.CSSProperties,
};

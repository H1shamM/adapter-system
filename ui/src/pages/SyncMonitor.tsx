import {useState, useEffect} from "react";
import {getSummary} from "../api/syncs";
import {RefreshCw} from "lucide-react";

type Summary = {
    last_status: string;
    last_run: string | null;
    last_duration_ms: number | null;
    success_rate: number;
    total_runs: number;
    failures: number;
};

export default function SyncMonitor() {
    const [data, setData] = useState<Record<string, Summary>>({});
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadSummary();
        const interval = setInterval(loadSummary, 10000);
        return () => clearInterval(interval);
    }, [])

    async function loadSummary() {
        try {
            const res = await getSummary();
            setData(res);
            setError(null);
        } catch (e) {
            console.error("Failed to load Summary", e);
            setError('Failed to load sync summary');
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return <div style={styles.loading}>Loading sync history...</div>;
    }

    if (error) {
        return (
            <div style={styles.errorContainer}>
                <p>{error}</p>
                <button onClick={loadSummary} style={styles.retryBtn}>Retry</button>
            </div>
        );
    }

    const entries = Object.entries(data);

    if (entries.length === 0) {
        return (
            <div style={styles.container}>
                <h2 style={styles.title}>Sync History</h2>
                <div style={styles.emptyState}>
                    No sync history yet. Trigger a sync to see results here.
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h2 style={styles.title}>Sync History</h2>
                <button onClick={loadSummary} style={styles.refreshBtn}>
                    <RefreshCw size={14}/>
                    Refresh
                </button>
            </div>

            <div style={styles.tableWrapper}>
                <table style={styles.table}>
                    <thead>
                    <tr style={styles.headerRow}>
                        <th style={styles.th}>Adapter</th>
                        <th style={styles.th}>Last Status</th>
                        <th style={styles.th}>Success Rate</th>
                        <th style={styles.th}>Duration</th>
                        <th style={styles.th}>Total Runs</th>
                        <th style={styles.th}>Failures</th>
                        <th style={styles.th}>Last Run</th>
                    </tr>
                    </thead>

                    <tbody>
                    {entries.map(([adapter, s]) => (
                        <tr key={adapter} style={styles.row}>
                            <td style={styles.td}>
                                <span style={styles.adapterId}>{adapter}</span>
                            </td>
                            <td style={styles.td}>
                                {statusBadge(s.last_status)}
                            </td>
                            <td style={styles.td}>
                                <span style={{
                                    ...styles.rateBadge,
                                    backgroundColor: s.success_rate >= 90 ? '#d1fae5' :
                                        s.success_rate >= 50 ? '#fef3c7' : '#fee2e2',
                                    color: s.success_rate >= 90 ? '#065f46' :
                                        s.success_rate >= 50 ? '#92400e' : '#991b1b',
                                }}>
                                    {s.success_rate}%
                                </span>
                            </td>
                            <td style={styles.td}>{formatDuration(s.last_duration_ms)}</td>
                            <td style={styles.td}>{s.total_runs}</td>
                            <td style={{
                                ...styles.td,
                                color: s.failures > 0 ? '#ef4444' : '#6b7280',
                                fontWeight: s.failures > 0 ? 600 : 400,
                            }}>
                                {s.failures}
                            </td>
                            <td style={styles.td}>{formatDate(s.last_run)}</td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

function statusBadge(status: string) {
    const colorMap: Record<string, {bg: string; color: string}> = {
        SUCCESS: {bg: '#d1fae5', color: '#065f46'},
        FAILED: {bg: '#fee2e2', color: '#991b1b'},
        STARTED: {bg: '#fef3c7', color: '#92400e'},
    };
    const style = colorMap[status] || {bg: '#f3f4f6', color: '#374151'};

    return (
        <span style={{
            padding: '3px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 600,
            backgroundColor: style.bg,
            color: style.color,
        }}>
            {status}
        </span>
    );
}

function formatDate(date: string | null) {
    if (!date) return "-";
    return new Date(date).toLocaleString();
}

function formatDuration(duration: number | null) {
    if (!duration) return "-";
    const seconds = duration / 1000;
    if (seconds >= 60) {
        return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
    }
    return `${seconds.toFixed(1)}s`;
}

const styles = {
    container: {
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    loading: {
        padding: '40px',
        textAlign: 'center' as const,
        color: '#6b7280',
    },
    errorContainer: {
        textAlign: 'center' as const,
        color: '#991b1b',
        padding: '40px',
    },
    retryBtn: {
        padding: '8px 16px',
        cursor: 'pointer',
    } as React.CSSProperties,
    emptyState: {
        textAlign: 'center' as const,
        color: '#6b7280',
        padding: '40px',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
    },
    title: {
        margin: 0,
        fontSize: '20px',
        fontWeight: 600,
    },
    refreshBtn: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '8px 14px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
    tableWrapper: {
        overflowX: 'auto' as const,
    },
    table: {
        width: '100%',
        borderCollapse: 'collapse' as const,
    },
    headerRow: {
        backgroundColor: '#f9fafb',
        borderBottom: '2px solid #e5e7eb',
    },
    th: {
        padding: '12px',
        textAlign: 'left' as const,
        fontSize: '12px',
        fontWeight: 600,
        color: '#6b7280',
        textTransform: 'uppercase' as const,
    },
    row: {
        borderBottom: '1px solid #f3f4f6',
    },
    td: {
        padding: '12px',
        fontSize: '14px',
    },
    adapterId: {
        fontFamily: 'monospace',
        fontSize: '13px',
        fontWeight: 500,
    },
    rateBadge: {
        padding: '3px 10px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 600,
    },
};

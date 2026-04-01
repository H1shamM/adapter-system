import {useEffect, useState} from 'react';
import {Activity, CheckCircle, XCircle, Clock} from 'lucide-react';
import {getSyncHistory} from '../api/syncs';


interface SyncRecord {
    sync_id: string;
    adapter: string;
    status: string;
    started_at: string;
    finished_at: string | null;
    duration_ms: number | null;
}

export default function LiveSyncMonitor() {
    const [syncs, setSyncs] = useState<SyncRecord[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadSyncs();
        const interval = setInterval(loadSyncs, 3000)
        return () => clearInterval(interval);
    }, []);

    async function loadSyncs() {
        try {
            const data = await getSyncHistory(50);
            setSyncs(Array.isArray(data) ? data : []);
            setError(null);
        } catch (err) {
            console.error('Failed to load syncs', err);
            setError('Failed to load sync history');
        } finally {
            setLoading(false);
        }
    }

    const activeSyncs = syncs.filter(sync => sync.status === 'STARTED');
    const recentCompleted = syncs.filter(sync => sync.status !== 'STARTED');

    if (loading) {
        return <div style={styles.loading}>Loading sync monitor...</div>;
    }

    if (error) {
        return (
            <div style={{...styles.container, textAlign: 'center' as const, color: '#991b1b', padding: '40px'}}>
                <p>{error}</p>
                <button onClick={loadSyncs} style={{padding: '8px 16px', cursor: 'pointer'}}>Retry</button>
            </div>
        );
    }

    if (syncs.length === 0) {
        return (
            <div style={styles.container}>
                <h2 style={styles.title}>📈 Live Sync Monitor</h2>
                <div style={{textAlign: 'center' as const, color: '#6b7280', padding: '24px'}}>
                    No sync history yet. Trigger a sync to see activity here.
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h2 style={styles.title}>📈 Live Sync Monitor</h2>

            {/* Active Syncs Section */}
            {activeSyncs.length > 0 && (
                <div style={styles.section}>
                    <h3 style={styles.sectionTitle}>
                        <Activity size={18} color="#10b981"/>
                        Active Syncs ({activeSyncs.length})
                    </h3>
                    <div style={styles.activeSyncsGrid}>
                        {activeSyncs.map(sync => (
                            <ActiveSyncCard key={sync.sync_id} sync={sync}/>
                        ))}
                    </div>
                </div>
            )}

            {/* Recent Completed Section */}
            <div style={styles.section}>
                <h3 style={styles.sectionTitle}>Recent Completed</h3>
                <div style={styles.tableWrapper}>
                    <table style={styles.table}>
                        <thead>
                        <tr style={styles.headerRow}>
                            <th style={styles.th}>Adapter</th>
                            <th style={styles.th}>Status</th>
                            <th style={styles.th}>Duration</th>
                            <th style={styles.th}>Started</th>
                            <th style={styles.th}>Finished</th>
                        </tr>
                        </thead>
                        <tbody>
                        {recentCompleted.map(sync => (
                            <tr key={sync.sync_id} style={styles.row}>
                                <td style={styles.td}>
                                    <span style={styles.adapterId}>{sync.adapter}</span>
                                </td>
                                <td style={styles.td}>
                                    {getStatusIcon(sync.status)}
                                </td>
                                <td style={styles.td}>
                                    {formatDuration(sync.duration_ms)}
                                </td>
                                <td style={styles.td}>
                                    {formatTime(sync.started_at)}
                                </td>
                                <td style={styles.td}>
                                    {formatTime(sync.finished_at)}
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function ActiveSyncCard({sync}: { sync: SyncRecord }) {
    const [elapsed, setElapsed] = useState<number>(0);

    useEffect(() => {
        const interval = setInterval(() => {
            const start = new Date(sync.started_at).getTime();
            const now = new Date().getTime();
            setElapsed(Math.floor((now - start) / 1000))
        }, 1000);

        return () => clearInterval(interval);
    }, [sync.started_at]);

    const estimatedTotal = 30 * 60;
    const progress = Math.min((elapsed / estimatedTotal) * 100, 99);

    return (
        <div style={styles.activeCard}>
            <div style={styles.activeCardHeader}>
                <span style={styles.activeCardTitle}>{sync.adapter}</span>
                <span style={styles.activeCardBadge}>
                    <Activity size={12} />
                    Syncing
                </span>
            </div>

            {/* Progress bar */}
            <div style={styles.progressBar}>
                <div
                    style={{
                        ...styles.progressFill,
                        width: `${progress}%`
                    }}
                />
            </div>

            <div style={styles.activeCardFooter}>
                <span style={styles.elapsed}>
                    <Clock size={14} />
                    {formatElapsed(elapsed)}
                </span>
                <span style={styles.progress}>{progress.toFixed(0)}%</span>
            </div>
        </div>
    );

}

// Helper: Returns status icon JSX
function getStatusIcon(status: string) {
    if (status === 'SUCCESS') {
        return (
            <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle size={16} />
                Success
            </span>
        );
    }
    if (status === 'FAILED') {
        return (
            <span style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <XCircle size={16} />
                Failed
            </span>
        );
    }
    return <span style={{ color: '#f59e0b' }}>{status}</span>;
}

// Helper: Format milliseconds to readable duration
function formatDuration(ms: number | null): string {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
}

// Helper: Format elapsed seconds
function formatElapsed(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
}

// Helper: Format timestamp to time
function formatTime(dateStr: string | null): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleTimeString();
}

// Styles
const styles = {
    container: {
        marginTop: '32px',
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
    title: {
        margin: '0 0 20px 0',
        fontSize: '20px',
        fontWeight: 600,
    },
    section: {
        marginBottom: '24px',
    },
    sectionTitle: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '16px',
        fontWeight: 600,
        marginBottom: '16px',
    },
    activeSyncsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '16px',
    },
    activeCard: {
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
    },
    activeCardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
    },
    activeCardTitle: {
        fontSize: '14px',
        fontWeight: 600,
        fontFamily: 'monospace',
    },
    activeCardBadge: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '12px',
        color: '#10b981',
        backgroundColor: '#d1fae5',
        padding: '4px 8px',
        borderRadius: '4px',
    },
    progressBar: {
        width: '100%',
        height: '8px',
        backgroundColor: '#e5e7eb',
        borderRadius: '4px',
        overflow: 'hidden' as const,
        marginBottom: '8px',
    },
    progressFill: {
        height: '100%',
        backgroundColor: '#10b981',
        transition: 'width 1s ease',
    },
    activeCardFooter: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    elapsed: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '12px',
        color: '#6b7280',
    },
    progress: {
        fontSize: '12px',
        fontWeight: 600,
        color: '#10b981',
    },
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
    },
};
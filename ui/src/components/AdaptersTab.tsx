import {useEffect, useState} from 'react';
import {getAdapterInstances, triggerSync} from '../api/adapters';
import {getAdapterHealth} from '../api/adapters';
import {HealthBadge} from './HealthBadge';
import {Settings, Play, RefreshCw} from 'lucide-react';

interface AdapterInstance {
    adapter_id: string;
    adapter_type: string;
    enabled: boolean;
    priority: string;
    sync_interval: number;
    last_sync: string | null;
    next_sync: string | null;
}

interface GroupedAdapters {
    [type: string]: AdapterInstance[];
}

export default function AdaptersTab() {
    const [instances, setInstances] = useState<AdapterInstance[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadInstances();
    }, []);

    async function loadInstances() {
        setLoading(true);
        try {
            const data = await getAdapterInstances();
            setInstances(data.instances || []);
            setError(null);
        } catch (err) {
            console.error('Failed to load adapter instances', err);
            setError('Failed to load adapters');
        } finally {
            setLoading(false);
        }
    }

    const grouped: GroupedAdapters = {};
    for (const inst of instances) {
        const type = inst.adapter_type || 'unknown';
        if (!grouped[type]) grouped[type] = [];
        grouped[type].push(inst);
    }

    if (loading) {
        return <div style={styles.loading}>Loading adapters...</div>;
    }

    if (error) {
        return (
            <div style={styles.errorContainer}>
                <p>{error}</p>
                <button onClick={loadInstances} style={styles.retryBtn}>Retry</button>
            </div>
        );
    }

    if (instances.length === 0) {
        return (
            <div style={styles.emptyContainer}>
                No adapter instances configured. Use the API or setup script to add adapters.
            </div>
        );
    }

    return (
        <div>
            <div style={styles.header}>
                <span style={styles.subtitle}>
                    {instances.length} instances across {Object.keys(grouped).length} adapter types
                </span>
                <button onClick={loadInstances} style={styles.refreshBtn}>
                    <RefreshCw size={14}/>
                    Refresh
                </button>
            </div>

            {Object.entries(grouped).map(([type, typeInstances]) => (
                <div key={type} style={styles.typeSection}>
                    <h3 style={styles.typeTitle}>
                        <Settings size={16}/>
                        {type}
                        <span style={styles.typeCount}>{typeInstances.length} instance{typeInstances.length !== 1 ? 's' : ''}</span>
                    </h3>
                    <div style={styles.cardsGrid}>
                        {typeInstances.map(inst => (
                            <InstanceCard
                                key={inst.adapter_id}
                                instance={inst}
                                onSyncTriggered={loadInstances}
                            />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

interface InstanceCardProps {
    instance: AdapterInstance;
    onSyncTriggered: () => void;
}

function InstanceCard({instance, onSyncTriggered}: InstanceCardProps) {
    const [health, setHealth] = useState<"HEALTHY" | "UNHEALTHY" | "UNKNOWN" | "DISABLED">('UNKNOWN');
    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<{status: string; message: string} | null>(null);

    useEffect(() => {
        getAdapterHealth(instance.adapter_id)
            .then(data => setHealth(data.status))
            .catch(() => setHealth('UNKNOWN'));
    }, [instance.adapter_id]);

    async function handleSync() {
        setSyncing(true);
        setSyncResult(null);
        try {
            await triggerSync(instance.adapter_id);
            setSyncResult({status: 'success', message: 'Sync queued'});
            onSyncTriggered();
        } catch (err) {
            console.error('Sync failed', err);
            setSyncResult({status: 'error', message: 'Failed to trigger sync'});
        } finally {
            setSyncing(false);
        }
    }

    const priorityColors: Record<string, {bg: string; color: string}> = {
        high: {bg: '#fef3c7', color: '#92400e'},
        medium: {bg: '#dbeafe', color: '#1e40af'},
        low: {bg: '#e5e7eb', color: '#374151'},
    };
    const pStyle = priorityColors[instance.priority] || priorityColors.low;

    return (
        <div style={styles.card}>
            <div style={styles.cardHeader}>
                <span style={styles.cardId}>{instance.adapter_id}</span>
                <HealthBadge status={health}/>
            </div>

            <div style={styles.cardBody}>
                <div style={styles.cardRow}>
                    <span style={styles.cardLabel}>Priority</span>
                    <span style={{
                        ...styles.badge,
                        backgroundColor: pStyle.bg,
                        color: pStyle.color,
                    }}>
                        {instance.priority}
                    </span>
                </div>
                <div style={styles.cardRow}>
                    <span style={styles.cardLabel}>Status</span>
                    <span style={{
                        ...styles.badge,
                        backgroundColor: instance.enabled ? '#d1fae5' : '#fee2e2',
                        color: instance.enabled ? '#065f46' : '#991b1b',
                    }}>
                        {instance.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </div>
                <div style={styles.cardRow}>
                    <span style={styles.cardLabel}>Interval</span>
                    <span style={styles.cardValue}>{formatInterval(instance.sync_interval)}</span>
                </div>
                <div style={styles.cardRow}>
                    <span style={styles.cardLabel}>Last Sync</span>
                    <span style={styles.cardValue}>{formatDate(instance.last_sync)}</span>
                </div>
            </div>

            <div style={styles.cardFooter}>
                <button
                    onClick={handleSync}
                    disabled={syncing || !instance.enabled}
                    style={{
                        ...styles.syncBtn,
                        opacity: (syncing || !instance.enabled) ? 0.5 : 1,
                    }}
                >
                    <Play size={14}/>
                    {syncing ? 'Queuing...' : 'Sync Now'}
                </button>
            </div>

            {syncResult && (
                <div style={{
                    ...styles.syncResultBanner,
                    backgroundColor: syncResult.status === 'success' ? '#d1fae5' : '#fee2e2',
                    color: syncResult.status === 'success' ? '#065f46' : '#991b1b',
                }}>
                    {syncResult.message}
                </div>
            )}
        </div>
    );
}

function formatInterval(seconds: number): string {
    const hours = seconds / 3600;
    if (hours >= 24) return `${hours / 24}d`;
    if (hours >= 1) return `${hours}h`;
    return `${seconds / 60}m`;
}

function formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 0) {
        const hours = Math.abs(diff) / (1000 * 60 * 60);
        if (hours < 1) return 'in < 1h';
        return `in ${Math.floor(hours)}h`;
    }
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return '< 1h ago';
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

const styles = {
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
    emptyContainer: {
        textAlign: 'center' as const,
        color: '#6b7280',
        padding: '40px',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
    },
    subtitle: {
        fontSize: '14px',
        color: '#6b7280',
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
    retryBtn: {
        padding: '8px 16px',
        cursor: 'pointer',
    } as React.CSSProperties,
    typeSection: {
        marginBottom: '32px',
    },
    typeTitle: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '18px',
        fontWeight: 600,
        marginBottom: '16px',
        textTransform: 'capitalize' as const,
    },
    typeCount: {
        fontSize: '13px',
        fontWeight: 400,
        color: '#9ca3af',
    },
    cardsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '16px',
    },
    card: {
        backgroundColor: 'white',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        overflow: 'hidden' as const,
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '14px 16px',
        borderBottom: '1px solid #f3f4f6',
    },
    cardId: {
        fontFamily: 'monospace',
        fontSize: '13px',
        fontWeight: 600,
    },
    cardBody: {
        padding: '12px 16px',
    },
    cardRow: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '4px 0',
    },
    cardLabel: {
        fontSize: '13px',
        color: '#6b7280',
    },
    cardValue: {
        fontSize: '13px',
        fontWeight: 500,
    },
    badge: {
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 500,
    },
    cardFooter: {
        padding: '12px 16px',
        borderTop: '1px solid #f3f4f6',
    },
    syncBtn: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        width: '100%',
        justifyContent: 'center',
        padding: '8px',
        fontSize: '13px',
        fontWeight: 500,
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
    syncResultBanner: {
        padding: '8px 16px',
        fontSize: '12px',
        fontWeight: 500,
        textAlign: 'center' as const,
    },
};

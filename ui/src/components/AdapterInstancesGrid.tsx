import {useEffect, useState} from 'react';
import {Play, Clock} from 'lucide-react';
import {getAdapterInstances, triggerSync} from '../api/adapters';


interface AdapterInstances {
    adapter_id: string;
    adapter_type: string;
    enabled: boolean;
    priority: string;
    sync_interval: number;
    last_sync: string | null;
    next_sync: string | null;
    sync_status?: string;
}

export default function AdapterInstancesGrid() {

    const [instances, setInstances] = useState<AdapterInstances[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        loadInstances();
        const interval = setInterval(loadInstances, 10000)
        return () => clearInterval(interval)
    }, [])

    async function loadInstances() {
        try {
            const data = await getAdapterInstances();
            setInstances(data.instances || []);
            setError(null);
        } catch (err) {
            console.error('Failed to load instances', err);
            setError('Failed to load adapter instances');
        } finally {
            setLoading(false);
        }
    }

    async function handleTriggerSync(adapter_id: string) {
        try {
            await triggerSync(adapter_id);
            alert(`Sync triggered for ${adapter_id}`);
            loadInstances();
        } catch (error) {
            console.error('Failed to load instances', error);
            alert('Failed to trigger sync')
        }
    }

    const filteredInstances = filter === 'all'
        ? instances
        : instances.filter(inst => inst.priority === filter);


    if (loading) {
        return <div style={styles.loading}>Loading adapter instances...</div>;
    }

    if (error) {
        return (
            <div style={{...styles.container, textAlign: 'center' as const, color: '#991b1b', padding: '40px'}}>
                <p>{error}</p>
                <button onClick={loadInstances} style={{padding: '8px 16px', cursor: 'pointer'}}>Retry</button>
            </div>
        );
    }

    if (instances.length === 0) {
        return (
            <div style={{...styles.container, textAlign: 'center' as const, color: '#6b7280', padding: '40px'}}>
                No adapter instances configured. Use the API or setup script to add adapters.
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Header with filter buttons */}
            <div style={styles.header}>
                <h2 style={styles.title}>📋 Adapter Instances ({instances.length})</h2>
                <div style={styles.filters}>
                    <button
                        onClick={() => setFilter('all')}
                        style={{
                            ...styles.filterBtn,
                            ...(filter === 'all' ? styles.filterBtnActive : {})
                        }}
                    >
                        All ({instances.length})
                    </button>
                    <button
                        onClick={() => setFilter('high')}
                        style={{
                            ...styles.filterBtn,
                            ...(filter === 'high' ? styles.filterBtnActive : {})
                        }}
                    >
                        High Priority
                    </button>
                    <button
                        onClick={() => setFilter('medium')}
                        style={{
                            ...styles.filterBtn,
                            ...(filter === 'medium' ? styles.filterBtnActive : {})
                        }}
                    >
                        Medium
                    </button>
                    <button
                        onClick={() => setFilter('low')}
                        style={{
                            ...styles.filterBtn,
                            ...(filter === 'low' ? styles.filterBtnActive : {})
                        }}
                    >
                        Low
                    </button>
                </div>
            </div>

            {/* Table */}
            <div style={styles.tableWrapper}>
                <table style={styles.table}>
                    <thead>
                    <tr style={styles.headerRow}>
                        <th style={styles.th}>Adapter ID</th>
                        <th style={styles.th}>Type</th>
                        <th style={styles.th}>Status</th>
                        <th style={styles.th}>Priority</th>
                        <th style={styles.th}>Interval</th>
                        <th style={styles.th}>Last Sync</th>
                        <th style={styles.th}>Next Sync</th>
                        <th style={styles.th}>Actions</th>
                    </tr>
                    </thead>
                    <tbody>
                    {/* Map over filtered instances to create rows */}
                    {filteredInstances.map((instance) => (
                        <tr key={instance.adapter_id} style={styles.row}>
                            <td style={styles.td}>
                                <span style={styles.adapterId}>{instance.adapter_id}</span>
                            </td>
                            <td style={styles.td}>
                                <span style={styles.adapterType}>{instance.adapter_type}</span>
                            </td>
                            <td style={styles.td}>
                                {getStatusBadge(instance.enabled)}
                            </td>
                            <td style={styles.td}>
                                {getPriorityBadge(instance.priority)}
                            </td>
                            <td style={styles.td}>
                                    <span style={styles.interval}>
                                        <Clock size={14}/>
                                        {formatInterval(instance.sync_interval)}
                                    </span>
                            </td>
                            <td style={styles.td}>
                                {formatDate(instance.last_sync)}
                            </td>
                            <td style={styles.td}>
                                {formatDate(instance.next_sync)}
                            </td>
                            <td style={styles.td}>
                                <button
                                    onClick={() => handleTriggerSync(instance.adapter_id)}
                                    style={styles.actionBtn}
                                    title="Sync Now"
                                >
                                    <Play size={16}/>
                                </button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    );


}

function getStatusBadge(enabled: boolean) {
    return (
        <span style={{
            ...styles.badge,
            backgroundColor: enabled ? '#d1fae5' : '#fee2e2',
            color: enabled ? '#065f46' : '#991b1b',
        }}>
            {enabled ? '✅ Enabled' : '⛔ Disabled'}
        </span>
    );
}

// Helper function: Returns priority badge JSX
function getPriorityBadge(priority: string) {
    const colors = {
        high: {bg: '#fef3c7', color: '#92400e'},
        medium: {bg: '#dbeafe', color: '#1e40af'},
        low: {bg: '#e5e7eb', color: '#374151'},
    };

    const style = colors[priority as keyof typeof colors] || colors.low;

    return (
        <span style={{
            ...styles.badge,
            backgroundColor: style.bg,
            color: style.color,
        }}>
            {priority}
        </span>
    );
}

// Helper function: Converts seconds to readable format
function formatInterval(seconds: number): string {
    const hours = seconds / 3600;
    if (hours >= 24) return `${hours / 24}d`;
    if (hours >= 1) return `${hours}h`;
    return `${seconds / 60}m`;
}

// Helper function: Formats date as relative time
function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-';

    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    // If in future, show "in X hours"
    if (diff < 0) {
        const hours = Math.abs(diff) / (1000 * 60 * 60);
        if (hours < 1) return 'in < 1h';
        if (hours < 24) return `in ${Math.floor(hours)}h`;
        return `in ${Math.floor(hours / 24)}d`;
    }

    // If in past, show "X hours ago"
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return '< 1h ago';
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
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
    filters: {
        display: 'flex',
        gap: '8px',
    },
    filterBtn: {
        padding: '8px 16px',
        fontSize: '14px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
    filterBtnActive: {
        backgroundColor: '#3b82f6',
        color: 'white',
        borderColor: '#3b82f6',
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
        fontWeight: 500,
    },
    adapterType: {
        color: '#6b7280',
    },
    badge: {
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 500,
    },
    interval: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        color: '#6b7280',
    },
    actionBtn: {
        padding: '6px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        borderRadius: '4px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
    } as React.CSSProperties,
};
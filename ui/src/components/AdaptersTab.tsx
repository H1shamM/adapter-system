import {useEffect, useState} from 'react';
import {getAdapterInstances, getAdapterSchema, createAdapter, deleteAdapter} from '../api/adapters';
import {HealthBadge} from './HealthBadge';
import {AdapterConfigForm} from './AdapterConfigForm';
import {useAdapterSync} from '../hooks/useAdapterSync';
import {useAdapterConfig} from '../hooks/useAdapterConfig';
import {useAdapterHealth} from '../hooks/useAdapterHealth';
import {Settings, Play, RefreshCw, Plus, Trash2, X, CheckCircle, XCircle, ChevronDown, ChevronRight} from 'lucide-react';

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
    const [supportedTypes, setSupportedTypes] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [collapsedTypes, setCollapsedTypes] = useState<Set<string>>(new Set());

    useEffect(() => {
        loadInstances();
    }, []);

    async function loadInstances() {
        setLoading(true);
        try {
            const data = await getAdapterInstances();
            setInstances(data.instances || []);
            setSupportedTypes(data.supported_types || []);
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

    return (
        <div>
            <div style={styles.header}>
                <span style={styles.subtitle}>
                    {instances.length} instances across {Object.keys(grouped).length} adapter types
                </span>
                <div style={{display: 'flex', gap: '8px'}}>
                    <button
                        onClick={() => setShowCreateForm(true)}
                        style={styles.createBtn}
                    >
                        <Plus size={14}/>
                        Create Adapter
                    </button>
                    <button onClick={loadInstances} style={styles.refreshBtn}>
                        <RefreshCw size={14}/>
                        Refresh
                    </button>
                </div>
            </div>

            {showCreateForm && (
                <CreateAdapterPanel
                    supportedTypes={supportedTypes}
                    onCreated={() => {
                        setShowCreateForm(false);
                        loadInstances();
                    }}
                    onCancel={() => setShowCreateForm(false)}
                />
            )}

            {instances.length === 0 && !showCreateForm && (
                <div style={styles.emptyContainer}>
                    No adapter instances configured. Click "Create Adapter" to get started.
                </div>
            )}

            {Object.entries(grouped).map(([type, typeInstances]) => {
                const isCollapsed = collapsedTypes.has(type);
                return (
                    <div key={type} style={styles.typeSection}>
                        <h3
                            style={styles.typeTitle}
                            onClick={() => {
                                setCollapsedTypes(prev => {
                                    const next = new Set(prev);
                                    next.has(type) ? next.delete(type) : next.add(type);
                                    return next;
                                });
                            }}
                        >
                            {isCollapsed ? <ChevronRight size={16}/> : <ChevronDown size={16}/>}
                            <Settings size={16}/>
                            {type}
                            <span style={styles.typeCount}>{typeInstances.length} instance{typeInstances.length !== 1 ? 's' : ''}</span>
                        </h3>
                        {!isCollapsed && (
                            <div className="adapter-cards-grid">
                                {typeInstances.map(inst => (
                                    <InstanceCard
                                        key={inst.adapter_id}
                                        instance={inst}
                                        onChanged={loadInstances}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}

// --- Create Adapter Panel ---

interface CreateAdapterPanelProps {
    supportedTypes: string[];
    onCreated: () => void;
    onCancel: () => void;
}

function CreateAdapterPanel({supportedTypes, onCreated, onCancel}: CreateAdapterPanelProps) {
    const [selectedType, setSelectedType] = useState('');
    const [schema, setSchema] = useState<Record<string, unknown>>({});
    const [loadingSchema, setLoadingSchema] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleTypeSelect(type: string) {
        setSelectedType(type);
        setLoadingSchema(true);
        setError(null);
        try {
            const schemaData = await getAdapterSchema(type);
            setSchema(schemaData);
        } catch (err) {
            console.error('Failed to load schema', err);
            setError('Failed to load adapter schema');
        } finally {
            setLoadingSchema(false);
        }
    }

    async function handleSave(config: Record<string, unknown>) {
        setSaving(true);
        setError(null);
        try {
            await createAdapter({adapter_type: selectedType, ...config});
            onCreated();
        } catch (err) {
            console.error('Failed to create adapter', err);
            setError('Failed to create adapter');
        } finally {
            setSaving(false);
        }
    }

    return (
        <div style={styles.createPanel}>
            <div style={styles.createPanelHeader}>
                <h3 style={{margin: 0, fontSize: '16px', fontWeight: 600}}>Create New Adapter</h3>
                <button onClick={onCancel} style={styles.closeBtn}>
                    <X size={16}/>
                </button>
            </div>

            {error && (
                <div style={styles.formError}>{error}</div>
            )}

            <div style={styles.typeSelector}>
                <label style={styles.formLabel}>Adapter Type</label>
                <div style={styles.typeButtons}>
                    {supportedTypes.map(type => (
                        <button
                            key={type}
                            onClick={() => handleTypeSelect(type)}
                            style={{
                                ...styles.typeButton,
                                ...(selectedType === type ? styles.typeButtonActive : {}),
                            }}
                        >
                            {type}
                        </button>
                    ))}
                </div>
            </div>

            {loadingSchema && <div style={styles.loading}>Loading schema...</div>}

            {selectedType && Object.keys(schema).length > 0 && !loadingSchema && (
                <div style={{marginTop: '16px'}}>
                    <AdapterConfigForm
                        adapterName={selectedType}
                        config={{}}
                        schema={schema}
                        onSave={handleSave}
                    />
                    {saving && <div style={{marginTop: '8px', color: '#6b7280', fontSize: '13px'}}>Saving...</div>}
                </div>
            )}
        </div>
    );
}

// --- Instance Card ---

interface InstanceCardProps {
    instance: AdapterInstance;
    onChanged: () => void;
}

function InstanceCard({instance, onChanged}: InstanceCardProps) {
    const health = useAdapterHealth(instance.adapter_id);
    const sync = useAdapterSync(instance.adapter_id);
    const config = useAdapterConfig(instance.adapter_id);
    const [deleting, setDeleting] = useState(false);

    async function handleDelete() {
        if (!confirm(`Delete adapter "${instance.adapter_id}"? This cannot be undone.`)) return;
        setDeleting(true);
        try {
            await deleteAdapter(instance.adapter_id);
            onChanged();
        } catch (err) {
            console.error('Delete failed', err);
            alert('Failed to delete adapter');
        } finally {
            setDeleting(false);
        }
    }

    const priorityColors: Record<string, {bg: string; color: string}> = {
        high: {bg: '#fef3c7', color: '#92400e'},
        medium: {bg: '#dbeafe', color: '#1e40af'},
        low: {bg: '#e5e7eb', color: '#374151'},
    };
    const pStyle = priorityColors[instance.priority] || priorityColors.low;

    const taskStatus = sync.task?.status;
    const statusColor = taskStatus === 'SUCCESS' ? '#10b981'
        : taskStatus === 'FAILURE' ? '#ef4444'
        : taskStatus === 'STARTED' || taskStatus === 'RUNNING' ? '#f59e0b'
        : undefined;

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

            {/* Live sync task status */}
            {sync.task && (
                <div style={{padding: '8px 16px', fontSize: '13px', color: statusColor}}>
                    {taskStatus === 'SUCCESS' && (
                        <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
                            <CheckCircle size={14}/>
                            Sync completed
                            {sync.task.result && (
                                <span> ({sync.task.result.inserted} inserted, {sync.task.result.modified} updated)</span>
                            )}
                        </span>
                    )}
                    {taskStatus === 'FAILURE' && (
                        <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
                            <XCircle size={14}/>
                            Sync failed
                        </span>
                    )}
                    {(taskStatus === 'STARTED' || taskStatus === 'RUNNING') && (
                        <span>Syncing...</span>
                    )}
                </div>
            )}

            {sync.lastSyncAt && (
                <div style={{padding: '0 16px 8px', fontSize: '12px', color: '#6b7280'}}>
                    Last sync: {sync.lastSyncAt.toLocaleTimeString()}
                </div>
            )}

            {/* Inline config editor */}
            {config.isOpen && (
                <div style={{padding: '12px 16px', borderTop: '1px solid #f3f4f6'}}>
                    <AdapterConfigForm
                        adapterName={instance.adapter_type}
                        config={config.config}
                        schema={config.schema}
                        onSave={config.save}
                    />
                </div>
            )}

            <div style={styles.cardFooter}>
                <button
                    onClick={sync.sync}
                    disabled={sync.loading || !instance.enabled}
                    style={{
                        ...styles.syncBtn,
                        opacity: (sync.loading || !instance.enabled) ? 0.5 : 1,
                    }}
                >
                    <Play size={14}/>
                    {sync.loading ? 'Queuing...' : 'Sync Now'}
                </button>
                <button
                    onClick={config.isOpen ? config.close : config.open}
                    disabled={config.loading}
                    style={styles.configBtn}
                    title="Configure"
                >
                    <Settings size={14}/>
                </button>
                <button
                    onClick={handleDelete}
                    disabled={deleting}
                    style={styles.deleteBtn}
                    title="Delete adapter"
                >
                    <Trash2 size={14}/>
                </button>
            </div>
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
    createBtn: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '8px 14px',
        fontSize: '13px',
        fontWeight: 500,
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
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
    // Create panel
    createPanel: {
        backgroundColor: 'white',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    createPanelHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
    },
    closeBtn: {
        padding: '4px',
        border: 'none',
        backgroundColor: 'transparent',
        cursor: 'pointer',
        color: '#6b7280',
    } as React.CSSProperties,
    formError: {
        padding: '8px 12px',
        marginBottom: '12px',
        backgroundColor: '#fef2f2',
        color: '#991b1b',
        borderRadius: '6px',
        fontSize: '13px',
    },
    formLabel: {
        display: 'block',
        fontSize: '13px',
        fontWeight: 600,
        color: '#374151',
        marginBottom: '8px',
    },
    typeSelector: {
        marginBottom: '8px',
    },
    typeButtons: {
        display: 'flex',
        flexWrap: 'wrap' as const,
        gap: '8px',
    },
    typeButton: {
        padding: '6px 14px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        borderRadius: '6px',
        cursor: 'pointer',
        textTransform: 'capitalize' as const,
    } as React.CSSProperties,
    typeButtonActive: {
        backgroundColor: '#3b82f6',
        color: 'white',
        borderColor: '#3b82f6',
    },
    // Type sections
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
        cursor: 'pointer',
        userSelect: 'none' as const,
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
    // Instance cards
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
        display: 'flex',
        gap: '8px',
        padding: '12px 16px',
        borderTop: '1px solid #f3f4f6',
    },
    syncBtn: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        flex: 1,
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
    configBtn: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px',
        fontSize: '13px',
        backgroundColor: 'white',
        color: '#6b7280',
        border: '1px solid #e5e7eb',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
    deleteBtn: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px',
        fontSize: '13px',
        backgroundColor: 'white',
        color: '#ef4444',
        border: '1px solid #fecaca',
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

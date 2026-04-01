import {useEffect, useState} from "react";
import {Activity, Database, Clock, Zap, BarChart3, Settings, Package, Radio} from "lucide-react";
import {getAdapterInstances, triggerAllSyncs} from '../api/adapters';
import {getSyncHistory} from '../api/syncs';
import AdapterInstancesGrid from '../components/AdapterInstancesGrid';
import LiveSyncMonitor from '../components/LiveSyncMonitor';
import WorkerVisualization from '../components/WorkerVisualization';
import {AssetList} from '../components/AssetList';
import SyncMonitor from './SyncMonitor';
import AdaptersTab from '../components/AdaptersTab';


type TabId = 'overview' | 'adapters' | 'assets' | 'history';

interface TabDef {
    id: TabId;
    label: string;
    icon: React.ReactNode;
}

const TABS: TabDef[] = [
    {id: 'overview', label: 'Overview', icon: <Radio size={16}/>},
    {id: 'adapters', label: 'Adapters', icon: <Settings size={16}/>},
    {id: 'assets', label: 'Assets', icon: <Package size={16}/>},
    {id: 'history', label: 'Sync History', icon: <BarChart3 size={16}/>},
];

interface DashboardStats {
    totalAdapters: number;
    activeSyncs: number;
    queueDepth: number;
    capacity: number;
}

export default function Dashboard() {

    const [activeTab, setActiveTab] = useState<TabId>('overview');
    const [stats, setStats] = useState<DashboardStats>({
        totalAdapters: 0,
        activeSyncs: 0,
        queueDepth: 0,
        capacity: 40
    });

    const [error, setError] = useState<string | null>(null);
    const [triggeringAll, setTriggeringAll] = useState(false)

    useEffect(() => {
        loadDashboardStats();
        const interval = setInterval(loadDashboardStats, 5000)

        return () => clearInterval(interval);

    }, []);


    async function loadDashboardStats() {
        try {
            const [instances, syncs] = await Promise.all([
                getAdapterInstances(),
                getSyncHistory(200),
            ]);

            const activeSyncs = Array.isArray(syncs)
                ? syncs.filter((s: {status: string}) => s.status === 'STARTED').length
                : 0;

            setStats({
                totalAdapters: instances.total || 0,
                activeSyncs,
                queueDepth: 0,
                capacity: 40
            });
            setError(null);
        } catch (err) {
            console.error('Failed to load dashboard stats:', err);
            setError('Failed to connect to backend. Is the API running?');
        }
    }

    async function handleSyncAll() {
        if (!confirm('Trigger all adapters to sync now?')) return;

        setTriggeringAll(true);

        try {
            const result = await triggerAllSyncs();
            if (result.failed > 0) {
                alert(`Triggered ${result.succeeded}/${result.total} syncs. ${result.failed} failed.`);
            }
            loadDashboardStats();
        } catch (err) {
            console.error('Failed to trigger all sync!', err)
            alert('Failed to trigger syncs. Check console.')
        } finally {
            setTriggeringAll(false)
        }

    }

    function renderTabContent() {
        switch (activeTab) {
            case 'overview':
                return (
                    <>
                        <WorkerVisualization activeSyncs={stats.activeSyncs} capacity={stats.capacity}/>
                        <AdapterInstancesGrid/>
                        <LiveSyncMonitor/>
                    </>
                );
            case 'adapters':
                return <AdaptersTab/>;
            case 'assets':
                return <AssetList/>;
            case 'history':
                return <SyncMonitor/>;
        }
    }

    return (
        <div style={styles.container}>
            {/* Header with Sync All button */}
            <div style={styles.header}>
                <h1 style={styles.title}>Adapter System Dashboard</h1>
                <button
                    onClick={handleSyncAll}
                    disabled={triggeringAll}
                    style={styles.syncAllButton}
                >
                    {triggeringAll ? 'Triggering...' : '🚀 Sync All Adapters'}
                </button>
            </div>

            {/* Error Banner */}
            {error && (
                <div style={styles.errorBanner}>
                    {error}
                    <button onClick={loadDashboardStats} style={styles.retryBtn}>Retry</button>
                </div>
            )}

            {/* Stats Cards */}
            <div style={styles.statsGrid}>
                <StatCard
                    icon={<Database size={24}/>}
                    title="Total Adapters"
                    value={stats.totalAdapters}
                    subtitle="Configured instances"
                    color="#3b82f6"
                />
                <StatCard
                    icon={<Activity size={24}/>}
                    title="Active Syncs"
                    value={stats.activeSyncs}
                    subtitle="Currently syncing"
                    color="#10b981"
                />
                <StatCard
                    icon={<Clock size={24}/>}
                    title="Queue Depth"
                    value={stats.queueDepth}
                    subtitle="Tasks waiting"
                    color="#f59e0b"
                />
                <StatCard
                    icon={<Zap size={24}/>}
                    title="Capacity"
                    value={`${stats.activeSyncs}/${stats.capacity}`}
                    subtitle="Slots used"
                    color="#8b5cf6"
                />
            </div>

            {/* Tab Navigation */}
            <div style={styles.tabBar}>
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            ...styles.tab,
                            ...(activeTab === tab.id ? styles.tabActive : {}),
                        }}
                    >
                        {tab.icon}
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {renderTabContent()}
        </div>

    )

}

interface StatCardProps {
    icon: React.ReactNode,
    title: string,
    value: number | string;
    subtitle: string;
    color: string;
}

function StatCard({icon, title, value, subtitle, color}: StatCardProps) {

    return (
        <div style={{...styles.statCard, borderLeft: `4px solid ${color}`}}>
            <div style={{...styles.statIcon, color}}>{icon}</div>
            <div style={styles.statContent}>
                <div style={styles.statTitle}>{title}</div>
                <div style={styles.statValue}>{value}</div>
                <div style={styles.statSubtitle}>{subtitle}</div>
            </div>
        </div>
    );
}

const styles = {
    container: {
        padding: '24px',
        maxWidth: '1400px',
        margin: '0 auto',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
    },
    title: {
        margin: 0,
        fontSize: '28px',
        fontWeight: 700,
    },
    syncAllButton: {
        padding: '12px 24px',
        fontSize: '16px',
        fontWeight: 600,
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
    } as React.CSSProperties,
    errorBanner: {
        padding: '12px 16px',
        marginBottom: '20px',
        backgroundColor: '#fef2f2',
        color: '#991b1b',
        borderRadius: '8px',
        border: '1px solid #fecaca',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    retryBtn: {
        padding: '6px 12px',
        fontSize: '13px',
        backgroundColor: '#991b1b',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
    } as React.CSSProperties,
    statsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '24px',
    },
    statCard: {
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    statIcon: {
        padding: '12px',
        borderRadius: '8px',
        backgroundColor: '#f3f4f6',
    },
    statContent: {
        flex: 1,
    },
    statTitle: {
        fontSize: '14px',
        color: '#6b7280',
        marginBottom: '4px',
    },
    statValue: {
        fontSize: '28px',
        fontWeight: 700,
        marginBottom: '2px',
    },
    statSubtitle: {
        fontSize: '12px',
        color: '#9ca3af',
    },
    tabBar: {
        display: 'flex',
        gap: '4px',
        borderBottom: '2px solid #e5e7eb',
        marginBottom: '24px',
    },
    tab: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '10px 20px',
        fontSize: '14px',
        fontWeight: 500,
        color: '#6b7280',
        backgroundColor: 'transparent',
        border: 'none',
        borderBottom: '2px solid transparent',
        marginBottom: '-2px',
        cursor: 'pointer',
        transition: 'color 0.15s, border-color 0.15s',
    } as React.CSSProperties,
    tabActive: {
        color: '#3b82f6',
        borderBottomColor: '#3b82f6',
        fontWeight: 600,
    },
};

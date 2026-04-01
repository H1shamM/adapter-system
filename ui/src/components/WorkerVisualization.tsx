import {Cpu, Server} from 'lucide-react';

interface WorkerVisualizationProps {
    activeSyncs: number;
    capacity: number;
}

export default function WorkerVisualization({activeSyncs, capacity}: WorkerVisualizationProps) {
    const workers = 4;
    const concurrencyPerWorker = capacity / workers;

    const syncsPerWorker = Math.floor(activeSyncs / workers);
    const remainder = activeSyncs % workers;

    return (
        <div style={styles.container}>
            <h2 style={styles.title}>
                <Server size={20}/>
                Worker Distribution ({workers} workers × {concurrencyPerWorker} slots = {capacity} capacity)
            </h2>

            <div style={styles.workersGrid}>
                {/* Create 4 worker cards */}
                {Array.from({length: workers}, (_, i) => {
                    // Distribute remainder: first workers get extra sync
                    const workerActive = syncsPerWorker + (i < remainder ? 1 : 0);
                    return (
                        <WorkerCard
                            key={i}
                            workerNumber={i + 1}
                            active={workerActive}
                            capacity={concurrencyPerWorker}
                        />
                    );
                })}
            </div>

            {/* Legend */}
            <div style={styles.legend}>
                <div style={styles.legendItem}>
                    <div style={{...styles.legendBox, backgroundColor: '#10b981'}}/>
                    <span>Active Task</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{...styles.legendBox, backgroundColor: '#e5e7eb'}}/>
                    <span>Empty Slot</span>
                </div>
            </div>
        </div>
    );

}

interface WorkerCardProps {
    workerNumber: number;
    active: number;
    capacity: number;
}

function WorkerCard({ workerNumber, active, capacity }: WorkerCardProps) {
    const utilization = (active / capacity) * 100;

    return (
        <div style={styles.workerCard}>
            <div style={styles.workerHeader}>
                <span style={styles.workerTitle}>
                    <Cpu size={16} />
                    Worker {workerNumber}
                </span>
                <span style={styles.workerUtil}>
                    {active}/{capacity}
                </span>
            </div>

            {/* Grid of 10 slots (5 columns × 2 rows) */}
            <div style={styles.slotsGrid}>
                {Array.from({ length: capacity }, (_, i) => (
                    <div
                        key={i}
                        style={{
                            ...styles.slot,
                            backgroundColor: i < active ? '#10b981' : '#e5e7eb'
                        }}
                        title={i < active ? 'Running' : 'Empty'}
                    />
                ))}
            </div>

            {/* Progress bar */}
            <div style={styles.progressBar}>
                <div
                    style={{
                        ...styles.progressFill,
                        width: `${utilization}%`,
                        // Color changes based on utilization
                        backgroundColor:
                            utilization > 90 ? '#ef4444' :   // Red if >90%
                                utilization > 70 ? '#f59e0b' :   // Orange if >70%
                                    '#10b981'                         // Green otherwise
                    }}
                />
            </div>

            <div style={styles.workerFooter}>
                <span style={styles.utilizationText}>
                    {utilization.toFixed(0)}% Utilization
                </span>
            </div>
        </div>
    );
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
    title: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        margin: '0 0 20px 0',
        fontSize: '20px',
        fontWeight: 600,
    },
    workersGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '20px',
    },
    workerCard: {
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
    },
    workerHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
    },
    workerTitle: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '14px',
        fontWeight: 600,
    },
    workerUtil: {
        fontSize: '14px',
        fontWeight: 700,
        color: '#6b7280',
    },
    slotsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',  // 5 columns
        gap: '6px',
        marginBottom: '12px',
    },
    slot: {
        aspectRatio: '1',  // Square shape
        borderRadius: '4px',
        transition: 'background-color 0.3s',
    },
    progressBar: {
        width: '100%',
        height: '6px',
        backgroundColor: '#e5e7eb',
        borderRadius: '3px',
        overflow: 'hidden' as const,
        marginBottom: '8px',
    },
    progressFill: {
        height: '100%',
        transition: 'width 0.3s ease, background-color 0.3s',
    },
    workerFooter: {
        textAlign: 'center' as const,
    },
    utilizationText: {
        fontSize: '12px',
        color: '#6b7280',
        fontWeight: 500,
    },
    legend: {
        display: 'flex',
        justifyContent: 'center',
        gap: '24px',
        paddingTop: '16px',
        borderTop: '1px solid #e5e7eb',
    },
    legendItem: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '14px',
        color: '#6b7280',
    },
    legendBox: {
        width: '16px',
        height: '16px',
        borderRadius: '4px',
    },
};
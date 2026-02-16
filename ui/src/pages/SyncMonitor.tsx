import {useState, useEffect} from "react";
import {getSummary} from "../api/syncs";

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

    useEffect(() => {
        loadSummary();
    }, [])

    async function loadSummary() {
        setLoading(true);
        try {
            const res = await getSummary();
            setData(res);
        } catch (e) {
            console.error("Failed to load Summary", e);

        } finally {
            setLoading(false);
        }
    }

    if (loading) return <p>Loading monitor ...</p>

    return (
        <div style={{padding: 20}}>
            <h2>Sync Monitor</h2>

            <table>
                <thead>
                <tr>
                    <th>Adapter</th>
                    <th>Status</th>
                    <th>Success %</th>
                    <th>Duration</th>
                    <th>Runs</th>
                    <th>Failures</th>
                    <th>Last Run</th>
                </tr>
                </thead>

                <tbody>
                {Object.entries(data).map(([adapter, s]) => (
                    <tr key={adapter}>
                        <td>{adapter}</td>
                        <td>{statusBadge(s.last_status)}</td>
                        <td>{s.success_rate}</td>
                        <td>{formatDuration(s.last_duration_ms)}</td>
                        <td>{s.total_runs}</td>
                        <td>{s.failures}</td>
                        <td>{formatDate(s.last_run)}</td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    )
}

function statusBadge(status: string) {
    const color =
        status === "SUCCESS"
            ? "green"
            : status === "FAILED"
                ? "red"
                : "orange";

    return <span style={{color: color, fontWeight: 600}}>{status}</span>;

}

function formatDate(date: string | null) {
    if (!date) return "-";
    return new Date(date).toLocaleDateString();
}

function formatDuration(duration: number | null) {
    if (!duration) return "-";
    return `${(duration/1000).toFixed(2)}s`;
}
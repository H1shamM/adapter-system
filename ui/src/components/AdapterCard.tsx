import {HealthBadge} from "./HealthBadge.tsx";
import "../App.css"
import {AdapterConfigForm} from "./AdapterConfigForm.tsx";
import {useAdapterHealth} from "../hooks/useAdapterHealth.ts";
import {useAdapterConfig} from "../hooks/useAdapterConfig.ts";
import {useAdapterSync} from "../hooks/useAdapterSync.ts";


function getStatusColor(status: string) {
    switch (status) {
        case "SUCCESS":
            return "green"
        case "FAILURE":
            return "red"
        case "STARTED":
        case "RUNNING":
            return "orange"
        default:
            return "gray"
    }

}

type AdapterCardProps = {
    name: string
}

export function AdapterCard({name}: AdapterCardProps) {
    const healthStatus = useAdapterHealth(name)
    const config = useAdapterConfig(name)
    const sync = useAdapterSync(name)

    const color = getStatusColor(sync.task?.status || "STARTED")


    return (
        <div style={styles.card}>
            <h3>{name}</h3>
            <HealthBadge status={healthStatus}/>

            <button onClick={config.open}>
                Configure
            </button>

            {config.isOpen && (
                <AdapterConfigForm
                    adapterName={name}
                    config={config.config}
                    schema={config.schema}
                    onSave={config.save}
                />
            )}

            <button
                onClick={sync.sync}
                disabled={sync.loading}
                style={buttonStyle}
            >
                {sync.loading ? "Syncing..." : "Sync"}
            </button>

            {/* Status */}
            {sync.task && (
                <p style={{color}}>
                    {sync.loading && <span className="spinner"/>}
                    Status: <strong>{sync.task?.status || "IDLE"}</strong>
                </p>
            )}

            {/*Success message */}

            {sync.task?.status === "SUCCESS" && (
                <p style={{color: "green"}}>
                    ✔ Sync completed
                    {sync.task.result && (
                        <span>
                            {" "}
                            ({sync.task.result.inserted} inserted, {" "}
                            {sync.task.result.modified} updated)
                        </span>
                    )}
                </p>
            )}

            {/*Failure message */}

            {sync.task?.status === "FAILURE" && (
                <p style={{color: "red"}}>
                    ❌ Sync failed — check backend logs
                </p>
            )}


            {/* Last Sync Time */}
            {sync.lastSyncAt && (
                <p style={{fontSize: "12px", color: "#666"}}>
                    Last sync: {sync.lastSyncAt.toLocaleTimeString()}
                </p>
            )}


        </div>
    )
}

const styles = {
    card: {
        border: '1px solid #ddd',
        padding: '8px',
        borderRadius: '16px',
        width: '250px',
        boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
    },
}

const buttonStyle = {
    padding: '8px 12px',
    cursor: 'pointer',
}
type HealthStatus = "HEALTHY" | "UNKNOWN" | "UNHEALTHY" | "DISABLED"


export function HealthBadge({status}: { status: HealthStatus }) {
    const colorMap: Record<HealthStatus, string> = {
        HEALTHY: 'green',
        UNHEALTHY: 'red',
        UNKNOWN: 'grey',
        DISABLED: 'yellow'
    }


    return (
        <span style={{
            padding: "4px 8px",
            borderRadius: "6px",
            backgroundColor: colorMap[status],
            color: "white",
            fontSize: "12px",
        }}
        >
            {status}
        </span>
    )
}


import {useEffect, useState} from "react";
import {getAdapterHealth} from "../api/adapters.ts";

export type AdapterHealth = "HEALTHY" | "UNHEALTHY" | "UNKNOWN" | "DISABLED"

export function useAdapterHealth(name: string) {
    const [status, setStatus] = useState<AdapterHealth>("UNKNOWN")


    useEffect(() => {
        getAdapterHealth(name)
            .then((data) => {
                setStatus(data.status)
            })
            .catch(() => {
                setStatus("UNKNOWN")
            })
    }, [name])

    return status
}

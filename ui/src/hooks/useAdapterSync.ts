import {triggerSync} from "../api/adapters.ts";
import {useEffect, useState} from "react";
import {usePollTask} from "./usePollTask.ts";


export function useAdapterSync(adapterName: string) {
    const [taskId, setTaskId] = useState<string | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [lastSyncAt, setLastSyncAt] = useState<Date | null>(null)

    const task = usePollTask(taskId)


    async function sync() {
        setLoading(true)
        try {
            const result = await triggerSync(adapterName)
            setTaskId(result.sync_id)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (!task) return

        if (task.status === "SUCCESS" || task.status === "FAILURE") {
            setLastSyncAt(new Date())
        }
    }, [task])

    return {
        task,
        loading,
        lastSyncAt,
        sync,
    };

}
import {useEffect, useState} from "react"
import {api} from "../api/client.ts"

type TaskResult = {
    status: string,
    result?:{
        inserted: number,
        modified: number,
        success: boolean,
    }
}

export function usePollTask(taskId: string | null) {
    const [task, setTask] = useState<TaskResult | null>(null)

    useEffect(() => {
        if (!taskId) return

        const interval = setInterval(async () => {
            const res = await api.get(`/syncs/${taskId}`)

            setTask(res.data)
        },2000)

        return () => clearInterval(interval)
    }, [taskId])

    return task
}
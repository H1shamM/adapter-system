import {useEffect, useState} from "react";
import type {Asset} from "../types/asset.ts";
import {getAssets} from "../api/adapters.ts";


export function useAssets(page: number, limit: number) {

    const [assets, setAssets] = useState<Asset[]>([])
    const [total, setTotal] = useState<number>(0)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)


    useEffect(() => {

        let cancelled = false


        async function load() {
            setLoading(true)
            setError(null)

            try {
                const data = await getAssets({page, limit})
                if (!cancelled) {
                    setAssets(data.results)
                    setTotal(data.total)
                }
            } catch (err: any) {
                if (!cancelled) {
                    setError(err.message ?? "Failed to fetch assets")
                }

            } finally {
                if (!cancelled) {
                    setLoading(false)
                }
            }

        }

        load();

        return () => {
            cancelled = true
        }


    }, [page, limit]);

    return {
        assets,
        total,
        loading,
        error,
    }

}
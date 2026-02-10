import {api} from "./client.ts"

export async function fetchAssets() {
    try {
        const res = await api.get('/api/v1/assets')
        return res.data
    }
    catch (error) {
        console.log("Failed to fetch assets",error)
        return []
    }
}
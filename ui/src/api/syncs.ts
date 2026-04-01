import {api} from "./client.ts";

export async function getSummary ( ) {
    const res = await api.get("/syncs/summary");
    return res.data
}

export async function getSyncHistory(limit:number = 100) {
    const res = await api.get("/syncs/history", {params: {limit}})
    return res.data;
    
}
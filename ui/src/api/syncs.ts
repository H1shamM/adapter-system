import {api} from "./client.ts";

export async function getSummary ( ) {
    const res = await api.get("/syncs/summary");
    return res.data
}
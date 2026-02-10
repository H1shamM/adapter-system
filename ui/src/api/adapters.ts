import {api} from "./client.ts";
import type {AssetListResponse} from "../types/asset.ts";

export async function getAdapters() {
    const res = await api.get("api/v1/adapters");
    return res.data;
}

export async function getAdapterHealth(name: string) {
    const res = await api.post(`api/v1/adapters/${name}/health`);
    return res.data;
}

export async function triggerSync(adapter: string) {
    const res = await api.post(`api/v1/adapters/${adapter}/sync`)
    return res.data

}

export async function getAssets(params: {
    page: number,
    limit: number,
    asset_type?: string,
    status?: string,
}): Promise<AssetListResponse> {

    const res = await  api.get('/api/v1/assets',{
        params,
    })
    return res.data;
    
}

export async function fetchAdapterConfig(name: string) {
    const res = await api.get(`api/v1/adapters/${name}`)
    return res.data
}

export async function updateAdapterConfig(adapter_name: string, config: Record<string, unknown>) {
    const res = await api.post(`api/v1/adapters`, {
        name: adapter_name,
        ...config
    });

    return res.data
}

export async function getAdapterSchema(adapter_name: string) {
    const res = await api.get(`api/v1/adapters/${adapter_name}/schema`);
    return res.data
}
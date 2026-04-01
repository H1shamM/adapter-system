import {api} from "./client.ts";
import type {AssetListResponse} from "../types/asset.ts";

export async function getAdapters() {
    const res = await api.get("/adapters");
    return res.data;
}

export async function getAdapterHealth(name: string) {
    const res = await api.post(`/adapters/${name}/health`);
    return res.data;
}

export async function triggerSync(adapter_id: string) {
    const res = await api.post(`/adapters/${adapter_id}/sync`)
    return res.data

}

export async function getAssets(params: {
    page: number,
    limit: number,
    asset_type?: string,
    status?: string,
}): Promise<AssetListResponse> {

    const res = await api.get('/assets', {
        params,
    })
    return res.data;

}

export async function fetchAdapterConfig(name: string) {
    const res = await api.get(`/adapters/${name}`)
    return res.data
}

export async function updateAdapterConfig(adapter_name: string, config: Record<string, unknown>) {
    const res = await api.post(`/adapters`, {
        name: adapter_name,
        ...config
    });

    return res.data
}

export async function getAdapterSchema(adapter_name: string) {
    const res = await api.get(`/adapters/${adapter_name}/schema`);
    return res.data
}

export async function getAdapterInstances(adapterType?: string) {
    const params = adapterType ? {adapter_type: adapterType} : {};
    const  res = await api.get("/adapters", { params})

    return res.data
    
}

export async function triggerAllSyncs() {
    const instances = await getAdapterInstances();
    const results = await Promise.allSettled(
        instances.instances.map((inst: any) =>
            triggerSync(inst.adapter_id)
        )
    );

    const failed = results.filter(r => r.status === 'rejected');
    if (failed.length > 0) {
        console.warn(`${failed.length}/${results.length} sync triggers failed`);
    }

    return {
        total: results.length,
        succeeded: results.length - failed.length,
        failed: failed.length,
    };
}
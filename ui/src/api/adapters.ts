import {api} from "./client.ts";
import type {AssetListResponse} from "../types/asset.ts";

export async function getAdapterHealth(name: string) {
    const res = await api.post(`/adapters/${name}/health`);
    return res.data;
}

export async function triggerSync(adapter_id: string) {
    const res = await api.post(`/adapters/${adapter_id}/sync`);
    return res.data;
}

export async function getAssets(params: {
    page: number,
    limit: number,
    asset_type?: string,
    status?: string,
}): Promise<AssetListResponse> {
    const res = await api.get('/assets', {params});
    return res.data;
}

export async function fetchAdapterConfig(name: string) {
    const res = await api.get(`/adapters/${name}`);
    return res.data;
}

export async function createAdapter(config: Record<string, unknown>) {
    const res = await api.post('/adapters', config);
    return res.data;
}

export async function deleteAdapter(adapterId: string) {
    const res = await api.delete(`/adapters/${adapterId}`);
    return res.data;
}

export async function getAdapterSchema(adapterType: string) {
    const res = await api.get(`/adapters/${adapterType}/schema`);
    return res.data;
}

export async function getAdapterInstances(adapterType?: string) {
    const params = adapterType ? {adapter_type: adapterType} : {};
    const res = await api.get("/adapters", {params});
    return res.data;
}

export async function triggerAllSyncs() {
    const instances = await getAdapterInstances();
    const results = await Promise.allSettled(
        instances.instances.map((inst: {adapter_id: string}) =>
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

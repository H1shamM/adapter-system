import type {Asset} from "../types/asset.ts"
import type {ApiAsset} from "../types/apiAsset.ts";

export function mapApiAsset(raw: ApiAsset): Asset {
    const id = raw.id || raw.asset_id || '';
    const type = raw.type || raw.asset_type || '';
    const vendor = raw.data?.vendor || raw.vendor || '';
    const lastSeen = raw.data?.last_seen || raw.last_seen || '';
    const metadata = raw.data?.metadata || raw.metadata || {};
    const name = raw.data?.name || raw.name || resolveAssetName(raw, type, id, metadata);

    return {
        id,
        type,
        status: raw.status,
        vendor,
        last_seen: lastSeen,
        metadata,
        name,
    }
}

function isString(value: unknown): value is string {
    return typeof value === "string"
}

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null
}

function resolveAssetName(raw: ApiAsset, type: string, id: string, metadata: Record<string, unknown>): string {
    if (type === "user" && isObject(metadata)) {
        if (isString(metadata?.name)) {
            return metadata.name
        }
        if (isObject(metadata.name)) {
            const first = metadata.name.first;
            const last = metadata.name.last;
            if (isString(first) && isString(last)) {
                return `${first} ${last}`
            }
        }
    }

    if (type === "crypto") {
        const cryptoName = metadata?.["name"]
        return isString(cryptoName) ? cryptoName : id;
    }

    if (type === "issue") {
        return raw.name ?? id;
    }

    return id;
}

import type {Asset} from "../types/asset.ts"
import type {ApiAsset} from "../types/apiAsset.ts";

export function mapApiAsset(raw: ApiAsset): Asset {
    return {
        id:raw.asset_id,
        type: raw.asset_type,
        status:raw.status,
        vendor:raw.vendor,
        last_seen:raw.last_seen,
        metadata:raw.metadata?? {},
        name: resolveAssetName(raw),
    }

}

function isString(value: unknown): value is string {
    return typeof value === "string"
}

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null
}

function resolveAssetName(raw: ApiAsset): string {
    if (raw.name){
        return raw.name
    }
    const md = raw.metadata
    console.log("asset_type", raw.asset_type)
    if (raw.asset_type === "user" && isObject(md)){

        if (isString(md?.name)){
            return md.name
        }
        if (isObject(md.name)) {
            const first = md.name.first;
            const last = md.name.last;
            if (isString(first) && isString(last)) {
                return `${first} ${last}`
            }
        }
    }

    if (raw.asset_type === "crypto"){
        const cryptoName = raw.metadata?.["name"]
        return isString(cryptoName)? cryptoName: raw.asset_id;
    }

    if(raw.asset_type === "issue"){
        return raw.name ?? raw.asset_id;
    }

    return raw.asset_id;
}
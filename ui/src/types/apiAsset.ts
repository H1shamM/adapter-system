export interface ApiAsset{
    asset_id:string,
    asset_type: string,
    name?: string,
    status: string,
    vendor: string,
    last_seen?: string,
    metadata?: Record<string, unknown>,
}
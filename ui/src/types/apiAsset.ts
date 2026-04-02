export interface ApiAsset{
    id: string,
    type: string,
    name?: string,
    status: string,
    data?: {
        name?: string,
        vendor?: string,
        last_seen?: string,
        metadata?: Record<string, unknown>,
    },
    // Legacy flat fields (some endpoints may still use these)
    asset_id?: string,
    asset_type?: string,
    vendor?: string,
    last_seen?: string,
    metadata?: Record<string, unknown>,
}
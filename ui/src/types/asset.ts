export interface Asset {
    id: string
    name: string
    type: string
    status: string
    vendor: string
    last_seen: string
    metadata: Record<string, unknown>
}

export interface AssetListResponse {
    page: number
    limit: number
    total: number
    results: Asset[]
}

export interface Asset {
    id: string
    type: string
    status: string
    data: {
        name: string
        vendor: string
        last_seen: string
        metadata: Record<string, unknown>
    }

}

export interface AssetListResponse {
    page: number
    limit: number
    total: number
    results: Asset[]
}
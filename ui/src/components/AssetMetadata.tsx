import type {Asset} from "../types/asset.ts"


function getString(
    obj:Record<string, unknown>,
    key: string
): string | undefined {
    const value = obj[key]
    return typeof value === "string" ? value : undefined;
}

function getObject(
    obj:Record<string, unknown>,
    key: string
): Record<string, unknown> | undefined {
    const value = obj[key];
    return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
        : undefined;

}

function getNumber(
    obj:Record<string, unknown>,
    key: string
): number | undefined {
    const value = obj[key];
    return typeof value === "number" ? value : undefined;
}

export function AssetMetadata({asset}: {asset: Asset}) {
    switch (asset.type) {
        case "user":
            return <UserMetadata metadata={asset.data.metadata} />

        case "crypto":
            return <CryptoMetadata metadata={asset.data.metadata} />

        case "issue":
            return <IssueMetadata metadata={asset.data.metadata} />

        default:
            return <pre>{JSON.stringify(asset.data.metadata, null, 2)}</pre>
    }
}

function CryptoMetadata({metadata}: { metadata: Record<string, unknown>}) {
    const symbol = getString(metadata, "symbol");
    const price = getNumber(metadata, "current_price");
    const rank = getNumber(metadata, "market_cap_rank");

    return (
        <div>
            <strong>Symbol:</strong> {symbol?.toUpperCase()} <br/>
            <strong>Price:</strong>${price?.toLocaleString()}<br/>
            <strong>Market Cap Rank:</strong>#{rank}
        </div>

    )
}

function UserMetadata({metadata}: {metadata: Record<string, unknown> }) {
    const email = getString(metadata, "email");
    const phone = getString(metadata, "phone");

    const location = getObject(metadata, "location");
    const address = getObject(metadata, "address");

    const country =
        getString(location ?? {}, "country") ??
        getString(address ?? {}, "city");

    return (
        <div>
            <strong>Email:</strong>{email ?? "-"}<br/>
            <strong>Phone:</strong>{phone ?? "-"}<br/>
            <strong>Country</strong>{country ?? "-"}<br/>
        </div>
    )
}

function IssueMetadata({metadata}:{metadata:Record<string, unknown>}) {
    const url = getString(metadata, "url");

    if (!url) {
        return <div>No issue URL</div>
    }

    return (
        <div>
            <strong>URL:</strong>{" "}
            <a href={url} target="_blank" rel="noreferrer">
                Open Issue
            </a>
        </div>
    );
}
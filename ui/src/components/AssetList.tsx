import {useState} from 'react'

import * as React from "react";
import {AssetMetadata} from "./AssetMetadata.tsx";
import {getAssetIcon} from "./assetIcons.tsx";
import {useAssets} from "../hooks/useAssets.ts";


function getStatusColor(status: string) {

    switch (status.toLowerCase()) {
        case "success":
        case "active":
            return "#10b981"
        case "pending":
        case "running":
            return "#f59e0b"
        case "failed":
        case "error":
            return "#ef4444"
        default:
            return "#374151"
    }
}

export function AssetList() {
    const [page, setPage] = useState<number>(1)
    const limit = 25
    const [expandId, setExpandId] = useState<string | null>(null)

    const {assets, total, loading, error} = useAssets(page, limit)

    const totalPages = Math.ceil(total / limit)
    const canPrev = page > 1
    const canNext = page < totalPages

    function toggleRow(id: string) {
        setExpandId(prev => (prev === id ? null : id))
    }

    if (loading && assets.length === 0) {
        return <div style={styles.loading}>Loading assets...</div>;
    }

    if (error) {
        return (
            <div style={styles.errorContainer}>
                <p>{error}</p>
                <button onClick={() => setPage(1)} style={styles.retryBtn}>Retry</button>
            </div>
        );
    }

    if (!loading && assets.length === 0) {
        return (
            <div style={styles.emptyContainer}>
                No assets found. Run a sync to ingest data from your adapters.
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h2 style={styles.title}>All Assets</h2>
                <span style={styles.totalCount}>{total} total</span>
            </div>

            <div style={styles.tableWrapper}>
                <table style={styles.table}>
                    <thead>
                    <tr style={styles.headerRow}>
                        <th style={{...styles.th, width: 40}}></th>
                        <th style={styles.th}>ID</th>
                        <th style={styles.th}>Type</th>
                        <th style={styles.th}>Name</th>
                        <th style={styles.th}>Vendor</th>
                        <th style={styles.th}>Status</th>
                    </tr>
                    </thead>

                    <tbody>
                    {assets.map((a) => {
                        const isExpanded = expandId === a.id;
                        return (
                            <React.Fragment key={`asset-row-${a.id}`}>
                                <tr
                                    style={{...styles.row, cursor: "pointer"}}
                                    onClick={() => toggleRow(a.id)}
                                >
                                    <td style={{...styles.td, width: 40}}>
                                        {getAssetIcon(a.type)}
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.assetId}>{a.id}</span>
                                    </td>
                                    <td style={styles.td}>{a.type}</td>
                                    <td style={styles.td}>{a.name}</td>
                                    <td style={styles.td}>
                                        <span style={styles.vendorBadge}>{a.vendor}</span>
                                    </td>
                                    <td style={{
                                        ...styles.td,
                                        color: getStatusColor(a.status),
                                        fontWeight: 500,
                                    }}>
                                        {a.status}
                                    </td>
                                </tr>

                                {isExpanded && (
                                    <tr key={`asset-expanded-${a.id}`}>
                                        <td style={styles.expandedTd} colSpan={6}>
                                            <AssetMetadata asset={a}/>
                                        </td>
                                    </tr>
                                )}

                            </React.Fragment>
                        );
                    })}
                    </tbody>
                </table>
            </div>

            <div style={styles.pagination}>
                <button
                    disabled={!canPrev}
                    onClick={() => setPage(p => p - 1)}
                    style={{
                        ...styles.pageBtn,
                        opacity: canPrev ? 1 : 0.4,
                    }}
                >
                    Prev
                </button>

                <span style={styles.pageInfo}>
                    Page {page} of {totalPages}
                </span>

                <button
                    disabled={!canNext}
                    onClick={() => setPage(p => p + 1)}
                    style={{
                        ...styles.pageBtn,
                        opacity: canNext ? 1 : 0.4,
                    }}
                >
                    Next
                </button>
            </div>
        </div>
    )
}

const styles = {
    container: {
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    loading: {
        padding: '40px',
        textAlign: 'center' as const,
        color: '#6b7280',
    },
    errorContainer: {
        textAlign: 'center' as const,
        color: '#991b1b',
        padding: '40px',
    },
    retryBtn: {
        padding: '8px 16px',
        cursor: 'pointer',
    } as React.CSSProperties,
    emptyContainer: {
        textAlign: 'center' as const,
        color: '#6b7280',
        padding: '40px',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
    },
    title: {
        margin: 0,
        fontSize: '20px',
        fontWeight: 600,
    },
    totalCount: {
        fontSize: '14px',
        color: '#6b7280',
    },
    tableWrapper: {
        overflowX: 'auto' as const,
    },
    table: {
        width: '100%',
        borderCollapse: 'collapse' as const,
    },
    headerRow: {
        backgroundColor: '#f9fafb',
        borderBottom: '2px solid #e5e7eb',
    },
    th: {
        padding: '12px',
        textAlign: 'left' as const,
        fontSize: '12px',
        fontWeight: 600,
        color: '#6b7280',
        textTransform: 'uppercase' as const,
    },
    row: {
        borderBottom: '1px solid #f3f4f6',
    },
    td: {
        padding: '12px',
        fontSize: '14px',
    },
    assetId: {
        fontFamily: 'monospace',
        fontSize: '12px',
        color: '#6b7280',
    },
    vendorBadge: {
        padding: '2px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        backgroundColor: '#f3f4f6',
        color: '#374151',
    },
    expandedTd: {
        padding: '16px 12px',
        backgroundColor: '#fafafa',
        borderBottom: '1px solid #e5e7eb',
    },
    pagination: {
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        justifyContent: 'flex-end',
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid #f3f4f6',
    },
    pageBtn: {
        padding: '6px 14px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        borderRadius: '6px',
        cursor: 'pointer',
    } as React.CSSProperties,
    pageInfo: {
        fontSize: '13px',
        color: '#6b7280',
    },
};

import {useState} from 'react'

import * as React from "react";
import {AssetMetadata} from "./AssetMetadata.tsx";
import {getAssetIcon} from "./assetIcons.tsx";
import {useAssets} from "../hooks/useAssets.ts";


function getStatusColor(status: string) {

    switch (status.toLowerCase()) {
        case "success":
        case "active":
            return "green"
        case "pending":
        case "running":
            return "orange"
        case "failed":
        case "error":
            return "red"
        default:
            return "#333"
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


    return (
        <div style={styles.container}>
            <h2>All Assets</h2>

            {loading && <p>Loading assets...</p>}
            {error && <p style={{color: "red"}}></p>}

            {!loading && assets.length === 0 && <p>No assets found.</p>}


            {assets.length > 0 && (
                <>
                    <table style={styles.table}>
                        <thead style={styles.thead}>
                        <tr>
                            <th style={styles.th}></th>
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
                                        style={{cursor: "pointer"}}
                                        onClick={() => toggleRow(a.id)}
                                    >
                                        <td style={{...styles.td, width: 32}}>
                                            {getAssetIcon(a.type)}
                                        </td>
                                        <td style={styles.td}>{a.id}</td>
                                        <td style={styles.td}>{a.type}</td>
                                        <td style={styles.td}>{a.data.name}</td>
                                        <td style={styles.td}>{a.data.vendor}</td>
                                        <td
                                            style={{
                                                ...styles.td,
                                                color: getStatusColor(a.status),
                                            }}
                                        >{a.status}</td>
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
                    <div style={styles.pagination}>
                        <button
                            disabled={!canPrev}
                            onClick={() => setPage(p => p - 1)}
                        >
                            ◀ Prev
                        </button>

                        <span>
                            Page {page} of {totalPages}
                        </span>
                        <button
                            disabled={!canNext}
                            onClick={() => setPage(p => p + 1)}
                        >
                            Next ▶
                        </button>
                    </div>
        </>
            )}


        </div>
    )
}

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        marginTop: 32,
    },
    pagination: {
        display: "flex",
        gap: 12,
        alignItems: "center",
        justifyContent: "flex-end",
        marginTop: 16,
    },
    table: {
        width: "100%",
        borderCollapse: "collapse" as const,
        fontFamily: "Arial , sans-serif",
        boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
    },
    thead: {
        // backgroundColor: "#f5f5f5",
    },
    th: {
        borderBottom: "2px solid #ddd",
        textAlign: "left" as const,
        padding: "12px",
    },
    td: {
        borderBottom: "1px solid #eee",
        padding: "12px",
    },
    tr: {
        transition: "background-color 0.2s ",
    },
    trHover: {
        // backgroundColor: "#f9f9f9",
    },
    expandedTd: {
        padding: "16px",
        // backgroundColor: "#fafafa",
        borderBottom: "1px solid #eee",
    }
}
import {
    User,
    Bitcoin,
    AlertCircle,
    Box
} from "lucide-react"

import type {ReactNode} from "react";

export function getAssetIcon(type: string): ReactNode {
    switch (type) {
        case "user":
            return <User size={18}></User>

        case "crypto":
            return <Bitcoin size={18}></Bitcoin>

        case "issue":
            return <AlertCircle size={18}/>
        default:
            return <Box size={18}/>
    }
}
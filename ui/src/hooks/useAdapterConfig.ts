import {fetchAdapterConfig, getAdapterSchema, createAdapter} from "../api/adapters.ts";
import {useState} from "react";

export function useAdapterConfig(adapterId: string) {

    const [isOpen, setIsOpen] = useState<boolean>(false)
    const [config, setConfig] = useState({})
    const [schema, setSchema] = useState({})
    const [loading, setLoading] = useState<boolean>(false)
    const [adapterType, setAdapterType] = useState<string>('')

    async function open() {
        setLoading(true)
        try {
            const configRes = await fetchAdapterConfig(adapterId)
            const type = configRes.adapter_type || ''
            setAdapterType(type)

            // Fetch schema using adapter TYPE, not adapter ID
            const schemaRes = await getAdapterSchema(type)

            setConfig(configRes.config || {})
            setSchema(schemaRes)
            setIsOpen(true)
        } finally {
            setLoading(false)
        }
    }

    async function save(newConfig: Record<string, unknown>) {
        await createAdapter({
            adapter_id: adapterId,
            adapter_type: adapterType,
            ...newConfig,
        })
        setIsOpen(false)
    }

    return {
        isOpen,
        loading,
        config,
        schema,
        open,
        save,
        close: () => setIsOpen(false)
    }
}

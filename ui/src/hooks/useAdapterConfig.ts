import {fetchAdapterConfig, getAdapterSchema, updateAdapterConfig} from "../api/adapters.ts";
import {useState} from "react";

export function useAdapterConfig (adapterName: string){

    const [isOpen, setIsOpen] = useState<boolean>(false)
    const [config, setConfig] = useState({})
    const [schema, setSchema] = useState({})
    const [loading, setLoading] = useState<boolean>(false)

    async function open() {
        setLoading(true)
       try {
           const configRes = await fetchAdapterConfig(adapterName)
           const schemaRes = await getAdapterSchema(adapterName)

           setConfig(configRes.config || {})
           setSchema(schemaRes)
           setIsOpen(true)
       }
       finally {
           setLoading(false)
       }
    }

    async function save(newConfig: Record<string, unknown>) {
        await updateAdapterConfig(adapterName, newConfig)
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
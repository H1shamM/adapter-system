import {useState} from "react";
import {renderField} from "../utils/renderField"
import type {FieldSchema} from "../types/fields.ts";


type AdapterSchema = Record<string, FieldSchema>
type AdapterFormState = Record<string, unknown>
type AdapterConfig = {
    name: string,
    enabled: boolean,

    sync_interval: number,
    priority: "low" | "medium" | "high",
    asset_types: string[]

    base_url: string,
    auth_type: "none" | "api_key" | "bearer" | "aws",
    auth_config: Record<string, unknown>,

    repo?: string,
    services?: string[],
}

function normalizeAdapterConfig(
    adapterName: string,
    form: AdapterFormState
): AdapterConfig {


    const normalized: AdapterConfig = {
        name: adapterName,
        enabled: Boolean(form.enabled),

        sync_interval: Number(form.sync_interval),
        priority: form.priority as AdapterConfig["priority"] ?? "medium",
        asset_types: Array.isArray(form.asset_types) ? form.asset_types : [],

        base_url: String(form.base_url),
        auth_type: form.auth_type as AdapterConfig["auth_type"] ?? "none",
        auth_config: (
            typeof form.auth_config === "object" &&
            form.auth_config !== null &&
            !Array.isArray(form.auth_config)
                ? (form.auth_config ) as Record<string, unknown>: {}
        ),


    };

    if (typeof form.repo === "string") {
        normalized.repo = form.repo
    }

    if (Array.isArray(form.services)) {
        normalized.services = form.services
    }

    return normalized
}

type Props = {
    adapterName: string,
    config: AdapterFormState
    schema: AdapterSchema
    onSave: (newConfig: AdapterConfig) => void
};

export function AdapterConfigForm({adapterName, config, schema, onSave}: Props) {
    const [localConfig, setLocalConfig] = useState<AdapterFormState>({
        ...config,
    });

    function updateField(name: string, value: unknown) {

        setLocalConfig(prev => ({
            ...prev,
            [name]: value,
        }));
    }

    return (
        <div style={{border: "1px solid #ccc", padding: "12px", marginTop: "8px"}}>
            {Object.entries(schema).map(([fieldName, fieldSchema]) => {
                if (
                    fieldName === "auth_config" &&
                    localConfig.auth_type === "none"
                ){
                    return null
                }

                const value =
                    localConfig[fieldName] ??
                    fieldSchema.default ??
                    "";

                return (
                    <div key={fieldName} style={{marginBottom: "8px"}}>
                        <label style={{display: "block", fontWeight: 500}}>
                            {fieldSchema.label ?? fieldName}
                        </label>
                        {renderField(fieldName, fieldSchema, value, (val) =>
                            updateField(fieldName, val)
                        )}

                    </div>
                );
            })}


            <button onClick={() => onSave(normalizeAdapterConfig(adapterName, localConfig))}>
                Save
            </button>
        </div>

    );
}
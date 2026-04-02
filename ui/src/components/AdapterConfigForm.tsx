import {useState, useEffect} from "react";
import {renderField} from "../utils/renderField"
import type {FieldSchema} from "../types/fields.ts";


type AdapterSchema = Record<string, FieldSchema>
type AdapterFormState = Record<string, unknown>

function buildDefaults(schema: AdapterSchema): AdapterFormState {
    const defaults: AdapterFormState = {};
    for (const [key, field] of Object.entries(schema)) {
        if (field.default !== undefined) {
            defaults[key] = field.default;
        } else if (field.type === "boolean") {
            defaults[key] = false;
        } else if (field.type === "number") {
            defaults[key] = 0;
        } else if (field.type === "multiselect") {
            defaults[key] = [];
        } else if (field.type === "object") {
            defaults[key] = field.fields ? buildDefaults(field.fields) : {};
        } else {
            defaults[key] = "";
        }
    }
    return defaults;
}

type Props = {
    adapterName: string,
    config: AdapterFormState
    schema: AdapterSchema
    onSave: (newConfig: Record<string, unknown>) => void
};

export function AdapterConfigForm({adapterName, config, schema, onSave}: Props) {
    const [localConfig, setLocalConfig] = useState<AdapterFormState>(() => ({
        ...buildDefaults(schema),
        ...config,
    }));

    // Re-init when schema changes (e.g. user selects a different adapter type)
    useEffect(() => {
        setLocalConfig(prev => ({
            ...buildDefaults(schema),
            ...config,
            ...prev,
        }));
    }, [schema]);

    function updateField(name: string, value: unknown) {
        setLocalConfig(prev => ({
            ...prev,
            [name]: value,
        }));
    }

    function handleSave() {
        // Pass through all fields from the form state — don't hardcode field names
        const payload: Record<string, unknown> = {
            name: adapterName,
        };

        for (const [key, fieldSchema] of Object.entries(schema)) {
            const value = localConfig[key];

            // Skip auth_config when auth_type is "none"
            if (key === "auth_config" && localConfig.auth_type === "none") {
                payload[key] = {};
                continue;
            }

            // Coerce types based on schema
            if (fieldSchema.type === "boolean") {
                payload[key] = Boolean(value);
            } else if (fieldSchema.type === "number") {
                payload[key] = Number(value) || fieldSchema.default || 0;
            } else if (fieldSchema.type === "multiselect") {
                payload[key] = Array.isArray(value) ? value : [];
            } else {
                payload[key] = value ?? fieldSchema.default ?? "";
            }
        }

        onSave(payload);
    }

    return (
        <div style={styles.container}>
            {Object.entries(schema).map(([fieldName, fieldSchema]) => {
                if (
                    fieldName === "auth_config" &&
                    localConfig.auth_type === "none"
                ) {
                    return null
                }

                const value =
                    localConfig[fieldName] ??
                    fieldSchema.default ??
                    "";

                return (
                    <div key={fieldName} style={styles.field}>
                        <label style={styles.label}>
                            {fieldSchema.label ?? fieldName}
                            {fieldSchema.required && <span style={styles.required}> *</span>}
                        </label>
                        {renderField(fieldName, fieldSchema, value, (val) =>
                            updateField(fieldName, val)
                        )}
                    </div>
                );
            })}

            <button onClick={handleSave} style={styles.saveBtn}>
                Save
            </button>
        </div>
    );
}

const styles = {
    container: {
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
    },
    field: {
        marginBottom: '14px',
    },
    label: {
        display: 'block',
        fontSize: '13px',
        fontWeight: 600,
        color: '#374151',
        marginBottom: '6px',
    },
    required: {
        color: '#ef4444',
    },
    saveBtn: {
        padding: '8px 20px',
        fontSize: '14px',
        fontWeight: 600,
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        marginTop: '8px',
    } as React.CSSProperties,
};

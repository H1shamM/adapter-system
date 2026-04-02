import type {FieldSchema} from "../types/fields.ts";

const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    fontSize: '14px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    outline: 'none',
    boxSizing: 'border-box',
    backgroundColor: 'white',
};

const selectStyle: React.CSSProperties = {
    ...inputStyle,
    cursor: 'pointer',
};

const checkboxWrapperStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#374151',
};

export function renderField(
    name: string,
    schema: FieldSchema,
    value: unknown,
    onChange: (value: unknown) => void
) {
    switch (schema.type) {
        case "string":
            return (
                <input
                    name={name}
                    type="text"
                    value={String(value ?? '')}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={schema.label || name}
                    style={inputStyle}
                />
            );
        case "number":
            return (
                <input
                    type="number"
                    value={value === '' || value === undefined ? '' : Number(value)}
                    onChange={(e) => onChange(Number(e.target.value))}
                    placeholder={schema.label || name}
                    style={inputStyle}
                />
            )
        case "boolean":
            return (
                <label style={checkboxWrapperStyle}>
                    <input
                        type="checkbox"
                        checked={Boolean(value)}
                        onChange={(e) => onChange(Boolean(e.target.checked))}
                        style={{width: '16px', height: '16px', cursor: 'pointer'}}
                    />
                    {Boolean(value) ? 'Yes' : 'No'}
                </label>
            )
        case "select":
            return (
                <select
                    value={String(value ?? '')}
                    onChange={(e) => onChange(e.target.value)}
                    style={selectStyle}
                >
                    {!value && <option value="">Select...</option>}
                    {schema.options?.map((opt) => (
                        <option key={opt} value={opt}>
                            {opt}
                        </option>
                    ))}
                </select>
            )
        case "object":
            return (
                <div style={{
                    border: "1px solid #e5e7eb",
                    padding: "12px",
                    borderRadius: "8px",
                    marginTop: "4px",
                    backgroundColor: "white",
                }}>
                    {Object.entries(schema.fields ?? {}).map(([fieldName, fieldSchema]) => {
                        const fieldValue =
                            typeof value === "object" && value !== null
                                ? (value as Record<string, unknown>)[fieldName] :
                                fieldSchema.default ?? ""

                        return (
                            <div key={fieldName} style={{marginBottom: "10px"}}>
                                <label style={{
                                    fontSize: "13px",
                                    display: "block",
                                    fontWeight: 500,
                                    color: '#374151',
                                    marginBottom: '4px',
                                }}>
                                    {fieldSchema.label ?? fieldName}
                                    {fieldSchema.required && <span style={{color: '#ef4444'}}> *</span>}
                                </label>
                                {renderField(
                                    fieldName,
                                    fieldSchema,
                                    fieldValue,
                                    (v) =>
                                        onChange({
                                            ...(typeof value === "object" && value !== null ? value : {}),
                                            [fieldName]: v,
                                        })
                                )}
                            </div>
                        )
                    })}
                </div>
            )
        case "multiselect":
            return (
                <select
                    multiple
                    value={Array.isArray(value) ? value.map(String) : []}
                    onChange={(e) =>
                        onChange(
                            Array.from(e.target.selectedOptions).map(o => o.value))}
                    style={{
                        ...selectStyle,
                        minHeight: '80px',
                    }}
                >
                    {schema.options?.map(opt => (
                        <option key={opt} value={opt}>
                            {opt}
                        </option>
                    ))}
                </select>
            )
        default:
            return null

    }
}

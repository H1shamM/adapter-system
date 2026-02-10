import type {FieldSchema} from "../types/fields.ts";

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
                    value={String(value)}
                    onChange={(e) => onChange(e.target.value)}
                />
            );
        case "number":
            return (
                <input
                    type="number"
                    value={Number(value)}
                    onChange={(e) => onChange(Number(e.target.value))}
                />
            )
        case "boolean":
            return (
                <input
                    type="checkbox"
                    checked={Boolean(value)}
                    onChange={(e) => onChange(Boolean(e.target.checked))}
                />
            )
        case "select":
            return (
                <select
                    value={String(value)}
                    onChange={(e) => onChange(e.target.value)}>
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
                    border: "1px solid #ddd",
                    padding: "8px",
                    borderRadius: "6px",
                    marginTop: "4px",
                }}>
                    {Object.entries(schema.fields ?? {}).map(([fieldName, fieldSchema]) => {


                        const fieldValue =
                            typeof value === "object" && value !== null
                                ? (value as Record<string, unknown>)[fieldName] :
                                fieldSchema.default ?? ""

                        return (
                            <div key={fieldName} style={{marginTop: "6px"}}>
                                <label style={{fontSize: "12px", display: "block"}}>
                                    {fieldSchema.label ?? fieldName}
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
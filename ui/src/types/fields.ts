export type FieldSchema = {
    type: "string" | "number" | "boolean" | "select" | "multiselect" | "object",
    label?: string;
    required?: boolean;
    options?: string[],
    default?: unknown;

    fields?: Record<string, FieldSchema>;
}


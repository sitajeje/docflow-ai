
export type ReviewStatus =
    | "pending_review"
    | "approved"
    | "rejected";

export type InvoiceFields = {
    vendor: string | null;
    invoice_number: string | null;
    invoice_date: string | null;
    subtotal: string | null;
    vat: string | null;
    total: string | null;
    currency: string | null;
};

export type ReviewItem = {
    id: string;
    status: ReviewStatus;
    method: "regex" | "llm";
    raw_fields: InvoiceFields;
    normalized_fields: InvoiceFields;
    field_errors: Record<string, string[]>;
    reviewer: string | null;
    created_at: string;
    reviewed_at: string | null;
};

export type ReviewEvent = {
    action: string;
    actor: string;
    details: Record<string, unknown>;
    created_at: string;
};

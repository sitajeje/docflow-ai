
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { InvoiceFields, ReviewItem } from "@/lib/types";

const editableFields: (keyof InvoiceFields)[] = [
    "vendor",
    "invoice_number",
    "invoice_date",
    "subtotal",
    "vat",
    "total",
    "currency",
];

export function ReviewEditor({
    review,
}: {
    review: ReviewItem;
}) {
    const router = useRouter();

    const [fields, setFields] = useState<InvoiceFields>(
        review.normalized_fields,
    );
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    const pending = review.status === "pending_review";
    const hasErrors = Object.keys(review.field_errors).length > 0;

    async function sendAction(
        action: "fields" | "approve" | "reject" | "notify",
        method: "POST" | "PATCH",
        body?: unknown,
    ) {
        setBusy(true);
        setError("");

        try {
        const response = await fetch(
            `/api/reviews/${review.id}/${action}`,
            {
            method,
            headers: body
                ? { "Content-Type": "application/json" }
                : undefined,
            body: body ? JSON.stringify(body) : undefined,
            },
        );

        if (!response.ok) {
            throw new Error(
            `Operation failed: HTTP ${response.status}`,
            );
        }

        router.refresh();
        } catch (err) {
        setError(
            err instanceof Error ? err.message : "Unexpected error",
        );
        } finally {
        setBusy(false);
        }
    }

    async function saveCorrections() {
        const changed = Object.fromEntries(
        editableFields
            .filter((key) => fields[key] !== review.normalized_fields[key])
            .map((key) => [key, fields[key]]),
        );

        if (Object.keys(changed).length === 0) return;

        await sendAction("fields", "PATCH", { fields: changed });
    }

    return (
        <section className="space-y-5 rounded-xl border p-6">
        <div>
            <h2 className="text-xl font-semibold">Review extracted fields</h2>
            <p className="text-sm text-gray-500">
            Status: {review.status}
            </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
            {editableFields.map((key) => (
            <label key={key} className="space-y-1">
                <span className="text-sm font-medium">{key}</span>
                <input
                value={fields[key] ?? ""}
                disabled={!pending || busy}
                onChange={(event) =>
                    setFields((previous) => ({
                    ...previous,
                    [key]: event.target.value,
                    }))
                }
                className="w-full rounded-lg border p-2 text-black disabled:bg-gray-100"
                />
                {review.field_errors[key]?.map((message, index) => (
                <p key={index} className="text-xs text-red-600">
                    {message}
                </p>
                ))}
            </label>
            ))}
        </div>

        {review.field_errors.business_rules?.map((message, index) => (
            <p key={index} className="text-sm text-red-600">
            {message}
            </p>
        ))}

        {error && <p role="alert" className="text-red-600">{error}</p>}

        {pending && (
            <div className="flex flex-wrap gap-3">
            <button
                disabled={busy}
                onClick={saveCorrections}
                className="rounded-lg border px-4 py-2 disabled:opacity-50"
            >
                Save corrections
            </button>

            <button
                disabled={busy || hasErrors}
                onClick={() =>
                sendAction("approve", "POST", {
                    reviewer: "local_demo_reviewer",
                    reason: "Verified against source document",
                })
                }
                className="rounded-lg bg-green-700 px-4 py-2 text-white disabled:opacity-50"
            >
                Approve
            </button>

            <button
                disabled={busy}
                onClick={() =>
                sendAction("reject", "POST", {
                    reviewer: "local_demo_reviewer",
                    reason: "Rejected after manual verification",
                })
                }
                className="rounded-lg bg-red-700 px-4 py-2 text-white disabled:opacity-50"
            >
                Reject
            </button>

            <button
                disabled={busy}
                onClick={() => sendAction("notify", "POST")}
                className="rounded-lg border px-4 py-2 disabled:opacity-50"
            >
                Notify reviewer
            </button>
            </div>
        )}
        </section>
    );
}

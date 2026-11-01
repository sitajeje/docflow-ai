
import Link from "next/link";
import { Suspense } from "react";
import { connection } from "next/server";

import { ReviewEditor } from "@/components/review-editor";
import { apiRequest } from "@/lib/api";
import type { ReviewEvent, ReviewItem } from "@/lib/types";

type PageProps = {
    params: Promise<{ id: string }>;
};

// Fetch and render the review detail at request time.
async function ReviewDetailContent({ params }: PageProps) {
    // Wait for an incoming request before rendering dynamic review data.
    await connection();
    const { id } = await params;

    const [review, source, events] = await Promise.all([
        apiRequest<ReviewItem>(`/review-items/${id}`),
        apiRequest<{ markdown: string }>(
        `/review-items/${id}/source`,
        ),
        apiRequest<ReviewEvent[]>(
        `/review-items/${id}/events`,
        ),
    ]);

    return (
        <main className="mx-auto max-w-6xl space-y-8 p-8">
        <header className="space-y-3">
            <Link href="/" className="text-sm text-blue-700">
            Back to invoices
            </Link>

            <h1 className="text-3xl font-bold">
            {review.normalized_fields.invoice_number ??
                "Unknown invoice"}
            </h1>

            <p className="text-gray-500">
            {review.normalized_fields.vendor ?? "Unknown vendor"}
            </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
            <section className="space-y-3 rounded-xl border p-6">
            <h2 className="text-xl font-semibold">
                Extracted source
            </h2>
            <p className="text-sm text-gray-500">
                Markdown produced by Docling
            </p>

            <pre className="max-h-[650px] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-gray-100 p-4 text-sm text-black">
                {source.markdown}
            </pre>
            </section>

            <ReviewEditor review={review} />
        </div>

        <section className="space-y-4 rounded-xl border p-6">
            <h2 className="text-xl font-semibold">
            Audit history
            </h2>

            {events.map((event, index) => (
            <div key={index} className="border-b pb-3">
                <p className="font-medium">{event.action}</p>

                <p className="text-sm text-gray-500">
                {event.actor} ·{" "}
                {new Date(event.created_at).toLocaleString("fr-FR", {
                    timeZone: "Europe/Paris",
            })}
                </p>

                <pre className="mt-2 whitespace-pre-wrap break-words text-xs text-gray-600">
                {JSON.stringify(event.details, null, 2)}
                </pre>
            </div>
            ))}
        </section>
        </main>
    );
}

export default function ReviewDetailPage({
    params,
}: PageProps) {
    return (
        <Suspense
        fallback={
            <main className="mx-auto max-w-6xl p-8">
            <p role="status" className="text-gray-500">
                Loading invoice review...
            </p>
            </main>
        }
        >
        <ReviewDetailContent params={params} />
        </Suspense>
    );
}

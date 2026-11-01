
import Link from "next/link";
import { Suspense } from "react";

import { UploadForm } from "@/components/upload-form";
import { apiRequest } from "@/lib/api";
import type { ReviewItem } from "@/lib/types";
import { connection } from "next/server";

// Fetch and render the latest review items.
async function RecentReviews() {
  // Wait for an incoming request before fetching live review data.
  await connection();
  let reviews: ReviewItem[] = [];
  let loadError = false;

  try {
    reviews = await apiRequest<ReviewItem[]>(
      "/review-items?limit=30",
    );
  } catch (error) {
    console.error("Failed to load reviews:", error);
    loadError = true;
  }

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Recent reviews</h2>

      {loadError && (
        <p role="alert" className="text-red-600">
          Unable to load reviews. Check the FastAPI server.
        </p>
      )}

      {!loadError && reviews.length === 0 && (
        <p className="text-gray-500">No invoices yet.</p>
      )}

      {!loadError && (
        <div className="space-y-2">
          {reviews.map((review) => (
            <Link
              key={review.id}
              href={`/reviews/${review.id}`}
              className="flex items-center justify-between rounded-lg border p-4 hover:bg-gray-50"
            >
              <div>
                <p className="font-medium">
                  {review.normalized_fields.invoice_number ??
                    "Unknown invoice"}
                </p>
                <p className="text-sm text-gray-500">
                  {review.normalized_fields.vendor ??
                    "Unknown vendor"}
                </p>
              </div>

              <div className="text-right">
                <p className="font-medium">
                  {review.normalized_fields.total ?? "—"} EUR
                </p>
                <p className="text-xs text-gray-500">
                  {review.status}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

export default function HomePage() {
  return (
    <main className="mx-auto w-full space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header className="space-y-2">
        <p className="text-sm font-medium text-blue-700">
          DOCFLOW AI
        </p>

        <h1 className="text-3xl font-bold">
          Invoice Workspace
        </h1>

        <p className="text-gray-500">
          Extract, validate and review invoices with AI.
        </p>
      </header>

      {/* Two equal-width columns on desktop */}
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
        {/* Left column: PDF upload */}
        <div className="min-w-0 max-w-[800px]">
          <UploadForm />
        </div>

        {/* Right column: review list */}
        <div className="min-w-0 max-w-[800px] rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <Suspense
            fallback={
              <section className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  Recent reviews
                </h2>
                <p role="status" className="text-gray-500">
                  Loading reviews...
                </p>
              </section>
            }
          >
            <RecentReviews />
          </Suspense>
        </div>
      </div>
    </main>
  );
}

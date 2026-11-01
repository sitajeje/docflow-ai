
"use client";

import { useRouter } from "next/navigation";
import { useState, type SubmitEvent } from "react";

export function UploadForm() {
    const router = useRouter();

    const [file, setFile] = useState<File | null>(null);
    const [method, setMethod] = useState<"regex" | "llm">("llm");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        if (!file || loading) return;

        setLoading(true);
        setError("");

        try {
        const body = new FormData();
        body.append("file", file);
        body.append("method", method);

        const response = await fetch("/api/upload", {
            method: "POST",
            body,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error ?? "Upload failed");
        }

        router.push(`/reviews/${data.id}`);
        } catch (err) {
        setError(
            err instanceof Error
            ? err.message
            : "Unexpected error",
        );
        } finally {
        setLoading(false);
        }
    }

    return (
        <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
        >
        <div className="space-y-1">
            <h2 className="text-xl font-semibold text-gray-900">
            Upload an invoice
            </h2>
            <p className="text-sm text-gray-500">
            Extract and validate invoice data from a PDF.
            </p>
        </div>

        {/* Accessible file input with a styled upload area */}
        <label
            htmlFor="invoice-file"
            className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-blue-300 bg-blue-50/50 px-6 py-10 text-center transition-colors hover:border-blue-500 hover:bg-blue-50 focus-within:ring-2 focus-within:ring-blue-500"
        >
            <input
            id="invoice-file"
            type="file"
            accept=".pdf,application/pdf"
            required
            disabled={loading}
            className="sr-only"
            onChange={(event) => {
                const selectedFile =
                event.currentTarget.files?.[0] ?? null;

                setFile(selectedFile);
                setError("");
            }}
            />

            <svg
            xmlns="http://www.w3.org/2000/svg"
            width="44"
            height="44"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
            className="text-blue-600"
            >
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 16V4m0 0L8 8m4-4 4 4M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"
            />
            </svg>

            <span className="font-semibold text-gray-900">
            {file
                ? "Change selected PDF"
                : "Choose a PDF invoice"}
            </span>

            <span className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white shadow-sm">
            Browse files
            </span>

            <span className="text-xs text-gray-500">
            PDF files only
            </span>
        </label>

        {/* Show the selected document */}
        {file && (
            <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-white text-xl">
                📄
            </div>

            <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-gray-900">
                {file.name}
                </p>
                <p className="text-xs text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
                </p>
            </div>

            <span className="text-sm font-medium text-green-700">
                Ready
            </span>
            </div>
        )}

        <label className="block space-y-2">
            <span className="text-sm font-medium text-gray-900">
            Extraction strategy
            </span>

            <select
            value={method}
            disabled={loading}
            onChange={(event) =>
                setMethod(
                event.target.value as "regex" | "llm",
                )
            }
            className="w-full rounded-lg border border-gray-300 bg-white p-3 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
            <option value="llm">Gemini AI</option>
            <option value="regex">
                Regex (known template)
            </option>
            </select>
        </label>

        {error && (
            <p
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
            {error}
            </p>
        )}

        <button
            type="submit"
            disabled={loading || !file}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-6 py-3 font-semibold text-white shadow-sm transition-colors hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
            {loading ? (
            <>
                <span
                className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                aria-hidden="true"
                />
                Processing document...
            </>
            ) : (
            "Upload & Extract"
            )}
        </button>
        </form>
    );
}

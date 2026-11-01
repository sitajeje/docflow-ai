
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.FASTAPI_URL;

export async function POST(request: NextRequest) {
    if (!API_URL || !process.env.DOCFLOW_API_KEY) {
        return NextResponse.json(
        { error: "Server configuration is missing" },
        { status: 500 },
        );
    }

    try {
        const form = await request.formData();
        const file = form.get("file");
        const method = form.get("method");

        if (!(file instanceof File)) {
        return NextResponse.json(
            { error: "PDF file is required" },
            { status: 400 },
        );
        }

        if (
        !file.name.toLowerCase().endsWith(".pdf") ||
        file.size === 0 ||
        file.size > 10 * 1024 * 1024
        ) {
        return NextResponse.json(
            { error: "Invalid PDF or file exceeds 10 MB" },
            { status: 400 },
        );
        }

        if (method !== "regex" && method !== "llm") {
        return NextResponse.json(
            { error: "Invalid extraction method" },
            { status: 400 },
        );
        }

        // Step 1: Parse the uploaded PDF with Docling
        const pdfForm = new FormData();
        pdfForm.append("file", file);

        const parseResponse = await fetch(
        `${API_URL}/documents/parse`,
        {
            method: "POST",
            body: pdfForm,
            cache: "no-store",
        },
        );

        if (!parseResponse.ok) {
        return NextResponse.json(
            { error: "PDF parsing failed" },
            { status: 422 },
        );
        }

        const parsed = (await parseResponse.json()) as {
        text: string;
        };

        // Step 2: Save extracted fields as a review item
        const reviewResponse = await fetch(
        `${API_URL}/review-items`,
        {
            method: "POST",
            headers: {
            "Content-Type": "application/json",
            "x-api-key": process.env.DOCFLOW_API_KEY,
            },
            body: JSON.stringify({
            markdown: parsed.text,
            method,
            }),
            cache: "no-store",
        },
        );

        if (!reviewResponse.ok) {
        return NextResponse.json(
            { error: "Invoice extraction or saving failed" },
            { status: 502 },
        );
        }

        const review = (await reviewResponse.json()) as {
        id: string;
        };

        return NextResponse.json({
        id: review.id,
        status: "saved",
        });
    } catch (error) {
        console.error("Upload workflow failed:", error);

        return NextResponse.json(
        { error: "Document processing request failed" },
        { status: 500 },
        );
    }
}

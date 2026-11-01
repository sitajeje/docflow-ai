
import "server-only";

const baseUrl = process.env.FASTAPI_URL;

type ApiOptions = {
    method?: "GET" | "POST" | "PATCH";
    body?: unknown;
    reviewer?: boolean;
};

export async function apiRequest<T>(
    path: string,
    options: ApiOptions = {},
): Promise<T> {
    if (!baseUrl) {
    throw new Error("FASTAPI_URL is missing");
    }

    const key = options.reviewer
        ? process.env.DOCFLOW_REVIEWER_KEY
        : process.env.DOCFLOW_API_KEY;

    if (!key) {
        throw new Error("DocFlow API credential is missing");
    }

    const response = await fetch(`${baseUrl}${path}`, {
        method: options.method ?? "GET",
        headers: {
        "Content-Type": "application/json",
        [options.reviewer ? "x-reviewer-key" : "x-api-key"]:
            key,
        },
        body:
        options.body === undefined
            ? undefined
            : JSON.stringify(options.body),
        cache: "no-store",
        signal: AbortSignal.timeout(20000),
    });

    if (!response.ok) {
        const message = await response.text();
        throw new Error(
        `FastAPI returned ${response.status}: ${message}`,
        );
    }

    return (await response.json()) as T;
}

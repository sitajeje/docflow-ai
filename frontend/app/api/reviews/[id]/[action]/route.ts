
import { NextRequest, NextResponse } from "next/server";
import { apiRequest } from "@/lib/api";

type Context = {
    params: Promise<{
        id: string;
        action: string;
    }>;
};

const allowedActions = ["fields", "approve", "reject", "notify"];

async function forward(
    request: NextRequest,
    context: Context,
    method: "POST" | "PATCH",
) {
    const { id, action } = await context.params;

    // Prevent arbitrary backend path forwarding
    if (
        !/^[0-9a-f-]{36}$/i.test(id) ||
        !allowedActions.includes(action)
    ) {
        return NextResponse.json(
        { error: "Invalid review action" },
        { status: 400 },
        );
    }

    const expectedMethod = action === "fields" ? "PATCH" : "POST";

    if (method !== expectedMethod) {
        return NextResponse.json(
        { error: "Method not allowed" },
        { status: 405 },
        );
    }

    try {
        const body =
        action === "notify" ? undefined : await request.json();

        const result = await apiRequest(
        `/review-items/${id}/${action}`,
        {
            method,
            body,
            reviewer: action !== "notify",
        },
        );

        return NextResponse.json(result);
    } catch (error) {
        console.error("Review action failed:", error);

        return NextResponse.json(
        { error: "Review operation failed" },
        { status: 502 },
        );
    }
    }

    export async function POST(
    request: NextRequest,
    context: Context,
    ) {
    return forward(request, context, "POST");
    }

    export async function PATCH(
    request: NextRequest,
    context: Context,
    ) {
    return forward(request, context, "PATCH");
}

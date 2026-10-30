
from fastapi import FastAPI
from backend.app.api.invoices import router as invoice_router
from backend.app.api.documents import router as document_router
from backend.app.api.reviews import (
    router as review_router,
)

app = FastAPI(
    title="DocFlow AI API",
    version="0.3.0",
    description="AI-powered document processing API",
)

app.include_router(invoice_router)
app.include_router(document_router)
app.include_router(review_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "docflow-ai",
        "version": "0.3.0",
    }

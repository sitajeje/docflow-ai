
from fastapi import FastAPI
from backend.app.api.invoices import router as invoice_router

app = FastAPI(
    title="DocFlow AI API",
    version="0.2.0",
    description="AI-powered document processing API",
)

app.include_router(invoice_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "docflow-ai",
        "version": "0.2.0",
    }

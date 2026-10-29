
from fastapi import APIRouter
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)
from backend.app.schemas.extraction import (
    ExtractionRequest,
    ExtractionResult,
)
from backend.app.services.invoice_extractor import (
    extract_invoice,
)
from backend.app.services.llm_extractor import (
    LLMExtractionError,
)
from backend.app.schemas.invoice import (
    Invoice,
    InvoiceValidationResult,
)
from backend.app.services.invoice_validator import (
    validate_invoice,
)

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


@router.post(
    "/validate",
    response_model=InvoiceValidationResult,
)
def validate_invoice_endpoint(
    invoice: Invoice,
) -> InvoiceValidationResult:
    return validate_invoice(invoice)

@router.post(
    "/extract",
    response_model=ExtractionResult,
)
def extract_invoice_endpoint(
    request: ExtractionRequest,
) -> ExtractionResult:
    try:
        return extract_invoice(
            markdown=request.markdown,
            method=request.method,
        )

    except LLMExtractionError as exc:
        logger.exception("Invoice LLM extraction failed")
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


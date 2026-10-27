
from fastapi import APIRouter

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

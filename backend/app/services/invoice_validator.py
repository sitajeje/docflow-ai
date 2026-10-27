
from decimal import Decimal

from backend.app.schemas.invoice import (
    Invoice,
    InvoiceValidationResult,
)


def validate_invoice(
    invoice: Invoice,
) -> InvoiceValidationResult:
    # Calculate the expected total
    expected_total = (
        invoice.subtotal + invoice.vat
    ).quantize(Decimal("0.01"))

    # Apply deterministic business rules
    is_valid = expected_total == invoice.total

    errors = []

    if not is_valid:
        errors.append(
            "Invoice total does not match "
            "subtotal plus VAT."
        )

    return InvoiceValidationResult(
        invoice_number=invoice.invoice_number,
        vendor=invoice.vendor,
        is_valid=is_valid,
        expected_total=expected_total,
        declared_total=invoice.total,
        errors=errors,
    )

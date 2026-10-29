
from typing import Literal

from backend.app.schemas.extraction import (
    ExtractionResult,
    RawInvoiceFields,
)
from backend.app.services.extraction_validator import (
    ExtractionValidationError,
    normalize_invoice,
    validate_extracted_invoice,
)
from backend.app.services.llm_extractor import (
    extract_invoice_llm,
)
from backend.app.services.regex_extractor import (
    extract_invoice_regex,
)


def extract_invoice(
    markdown: str,
    method: Literal["regex", "llm"],
) -> ExtractionResult:
    """Run extraction and deterministic validation."""
    if method == "regex":
        raw = extract_invoice_regex(markdown)
    else:
        raw = extract_invoice_llm(markdown)

    try:
        invoice = normalize_invoice(raw)
    except ExtractionValidationError:
        # Malformed extracted fields require manual review.
        invoice = normalize_invoice(
            RawInvoiceFields(
                vendor=None,
                invoice_number=None,
                invoice_date=None,
                subtotal=None,
                vat=None,
                total=None,
                currency=None,
            )
        )

        return ExtractionResult(
            status="review_required",
            method=method,
            invoice=invoice,
            errors=["Extracted fields could not be normalized."],
        )

    errors = validate_extracted_invoice(invoice)

    return ExtractionResult(
        status=(
            "review_required" if errors
            else "validated"
        ),
        method=method,
        invoice=invoice,
        errors=errors,
    )

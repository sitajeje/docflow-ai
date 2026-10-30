
from pydantic import ValidationError

from backend.app.schemas.extraction import (
    ExtractedInvoice,
    RawInvoiceFields,
)
from backend.app.services.extraction_validator import (
    normalize_amount,
    normalize_date,
    validate_extracted_invoice,
)


def normalize_with_errors(
    raw: RawInvoiceFields,
) -> tuple[ExtractedInvoice, dict[str, list[str]]]:
    """Normalize each field without discarding valid values."""
    values = raw.model_dump()
    errors: dict[str, list[str]] = {}

    for field in ("subtotal", "vat", "total"):
        try:
            values[field] = normalize_amount(values[field])
        except ValueError:
            values[field] = None
            errors[field] = ["Invalid monetary value."]

    try:
        values["invoice_date"] = normalize_date(
            values["invoice_date"]
        )
    except ValueError:
        values["invoice_date"] = None
        errors["invoice_date"] = ["Invalid date."]

    for field in ("vendor", "invoice_number"):
        value = values[field]
        values[field] = value.strip() if value else None

    if values["currency"]:
        values["currency"] = values["currency"].strip().upper()

    try:
        invoice = ExtractedInvoice.model_validate(values)
    except ValidationError as exc:
        for error in exc.errors():
            field = str(error["loc"][0])
            errors.setdefault(field, []).append(
                "Invalid field value."
            )
            values[field] = None

        invoice = ExtractedInvoice.model_validate(values)

    business_errors = validate_extracted_invoice(invoice)

    if business_errors:
        errors["business_rules"] = business_errors

    return invoice, errors

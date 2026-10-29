
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from backend.app.schemas.extraction import (
    ExtractedInvoice,
    RawInvoiceFields,
)


class ExtractionValidationError(ValueError):
    pass


def normalize_amount(value: str | None) -> Decimal | None:
    """Convert French or English amounts to Decimal."""
    if value is None or not value.strip():
        return None

    normalized = (
        value.replace("\u00a0", "")
        .replace("\u202f", "")
        .replace(" ", "")
        .replace("€", "")
        .replace("EUR", "")
        .strip()
    )

    if "," in normalized and "." in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "")
            normalized = normalized.replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ExtractionValidationError(
            f"Invalid amount: {value}"
        ) from exc

    if not amount.is_finite():
        raise ExtractionValidationError(
            "Amount must be finite."
        )

    if amount < 0 or amount.as_tuple().exponent < -2:
        raise ExtractionValidationError(
            "Amount must be non-negative "
            "with at most two decimal places."
        )

    return amount


def normalize_date(value: str | None) -> date | None:
    """Normalize supported invoice date formats."""
    if value is None or not value.strip():
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    raise ExtractionValidationError(
        f"Unsupported invoice date: {value}"
    )


def normalize_invoice(
    raw: RawInvoiceFields,
) -> ExtractedInvoice:
    """Transform raw model fields into typed data."""
    currency = (
        raw.currency.strip().upper()
        if raw.currency
        else None
    )

    try:
        return ExtractedInvoice(
            vendor=raw.vendor.strip() if raw.vendor else None,
            invoice_number=(
                raw.invoice_number.strip()
                if raw.invoice_number else None
            ),
            invoice_date=normalize_date(raw.invoice_date),
            subtotal=normalize_amount(raw.subtotal),
            vat=normalize_amount(raw.vat),
            total=normalize_amount(raw.total),
            currency=currency,
        )
    except ValidationError as exc:
        raise ExtractionValidationError(
            "Extracted invoice fields are invalid."
        ) from exc


def validate_extracted_invoice(
    invoice: ExtractedInvoice,
) -> list[str]:
    """Check required fields and monetary consistency."""
    errors = []

    if not invoice.vendor:
        errors.append("Missing vendor.")

    if not invoice.invoice_number:
        errors.append("Missing invoice number.")

    if invoice.invoice_date is None:
        errors.append("Missing invoice date.")

    if invoice.currency != "EUR":
        errors.append("Currency must be EUR.")

    amounts = (
        invoice.subtotal,
        invoice.vat,
        invoice.total,
    )

    if any(amount is None for amount in amounts):
        errors.append("Missing monetary fields.")
    elif invoice.subtotal + invoice.vat != invoice.total:
        errors.append(
            "Invoice total does not match subtotal plus VAT."
        )

    return errors

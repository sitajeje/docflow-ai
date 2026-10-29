
import re

from backend.app.schemas.extraction import RawInvoiceFields


def find_field(
    text: str,
    pattern: str,
) -> str | None:
    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def extract_invoice_regex(
    markdown: str,
) -> RawInvoiceFields:
    """Extract invoice fields from supported French invoice layouts."""

    amount = r"([0-9][0-9 \u00a0\u202f.,]*[ \t]*(?:€|EUR)?)"

    return RawInvoiceFields(
        vendor=find_field(
            markdown,
            r"Fournisseur[ \t]*:[ \t]*(.*?)"
            r"(?=[ \t]+(?:N[°o][ \t]*Facture|Facture|Date)[ \t]*:|$)",
        ),
        invoice_number=find_field(
            markdown,
            r"(?:N[°o][ \t]*Facture|Facture[ \t]*N[°o]|Facture)"
            r"[ \t]*:[ \t]*([A-Z0-9-]+)",
        ) or find_field(
            markdown,
            r"FACTURE[ \t]+N[°o][ \t]*([A-Z0-9-]+)",
        ),
        invoice_date=find_field(
            markdown,
            r"\bDate[ \t]*:[ \t]*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
        ),
        subtotal=find_field(
            markdown,
            rf"\bTotal[ \t]+HT[ \t]*:[ \t]*{amount}",
        ),
        vat=find_field(
            markdown,
            rf"\bTVA(?:[ \t]+\d+[ \t]*%)?[ \t]*:[ \t]*{amount}",
        ),
        total=find_field(
            markdown,
            rf"\bTotal[ \t]+TTC[ \t]*:[ \t]*{amount}",
        ),
        currency="EUR" if ("€" in markdown or "EUR" in markdown.upper()) else None,
    )

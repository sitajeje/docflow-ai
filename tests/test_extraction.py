
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.extraction import RawInvoiceFields
from backend.app.services.extraction_validator import (
    normalize_amount,
    normalize_invoice,
    validate_extracted_invoice,
)

client = TestClient(app)

SAMPLE_MARKDOWN = """
FACTURE N° INV-2026-001
Fournisseur : Demo Consulting SAS
Date : 27/10/2026
Total HT : 100,00 €
TVA 20 % : 20,00 €
Total TTC : 120,00 €
"""


def make_raw_invoice(**overrides):
    data = {
        "vendor": "Demo Consulting SAS",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-10-27",
        "subtotal": "100.00",
        "vat": "20.00",
        "total": "120.00",
        "currency": "EUR",
    }
    data.update(overrides)
    return RawInvoiceFields(**data)


def test_normalize_french_amount():
    result = normalize_amount("1 234,50 €")
    assert result == Decimal("1234.50")


def test_normalize_invoice_date():
    invoice = normalize_invoice(
        make_raw_invoice(invoice_date="27/10/2026")
    )
    assert invoice.invoice_date.isoformat() == "2026-10-27"


def test_invalid_total_requires_review():
    invoice = normalize_invoice(
        make_raw_invoice(total="130.00")
    )
    errors = validate_extracted_invoice(invoice)

    assert any("total does not match" in e for e in errors)


def test_regex_extract_api():
    response = client.post(
        "/invoices/extract",
        json={
            "method": "regex",
            "markdown": SAMPLE_MARKDOWN,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    assert data["invoice"]["total"] == "120.00"


def test_llm_extract_with_mock():
    with patch(
        "backend.app.services.invoice_extractor.extract_invoice_llm",
        return_value=make_raw_invoice(),
    ) as mock_llm:
        response = client.post(
            "/invoices/extract",
            json={
                "method": "llm",
                "markdown": SAMPLE_MARKDOWN,
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "validated"
    mock_llm.assert_called_once()


def test_llm_missing_fields_require_review():
    with patch(
        "backend.app.services.invoice_extractor.extract_invoice_llm",
        return_value=make_raw_invoice(
            invoice_number=None,
            total=None,
        ),
    ):
        response = client.post(
            "/invoices/extract",
            json={
                "method": "llm",
                "markdown": SAMPLE_MARKDOWN,
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "review_required"
    assert len(response.json()["errors"]) >= 1

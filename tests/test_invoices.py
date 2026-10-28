
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.invoice import Invoice
from backend.app.services.invoice_validator import (
    validate_invoice,
)

client = TestClient(app)


def make_invoice(**overrides):
    # Create reusable test data
    data = {
        "vendor": "Demo Consulting SAS",
        "invoice_number": "INV-2026-001",
        "subtotal": "100.00",
        "vat": "20.00",
        "total": "120.00",
    }

    data.update(overrides)
    return data


def test_valid_invoice():
    invoice = Invoice(**make_invoice())

    result = validate_invoice(invoice)

    assert result.is_valid is True
    assert result.expected_total == Decimal("120.00")
    assert result.errors == []


def test_invalid_total():
    invoice = Invoice(
        **make_invoice(total="130.00")
    )

    result = validate_invoice(invoice)

    assert result.expected_total == Decimal("120.00")
    assert result.is_valid is False
    assert len(result.errors) == 1


def test_api_valid_invoice():
    response = client.post(
        "/invoices/validate",
        json=make_invoice(),
    )

    assert response.status_code == 200
    assert response.json()["is_valid"] is True


def test_api_business_validation_failure():
    response = client.post(
        "/invoices/validate",
        json=make_invoice(total="130.00"),
    )

    assert response.status_code == 200
    assert response.json()["is_valid"] is False


def test_api_missing_field():
    data = make_invoice()
    del data["vendor"]

    response = client.post(
        "/invoices/validate",
        json=data,
    )

    assert response.status_code == 422


def test_api_negative_amount():
    response = client.post(
        "/invoices/validate",
        json=make_invoice(subtotal="-100.00"),
    )

    assert response.status_code == 422


def test_api_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_zero_vat():
    invoice = Invoice(
        **make_invoice(
            vat="0.00",
            total="100.00",
        )
    )

    result = validate_invoice(invoice)

    assert result.is_valid is True
    assert result.expected_total == Decimal("100.00")
    assert result.errors == []
    
def test_too_many_decimal_places():
    response = client.post(
        "/invoices/validate",
        json=make_invoice(subtotal="100.123"),
    )

    assert response.status_code == 422
    
def test_blank_vendor():
    response = client.post(
        "/invoices/validate",
        json=make_invoice(vendor="   "),
    )

    assert response.status_code == 422
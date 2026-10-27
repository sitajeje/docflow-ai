
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class Invoice(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    vendor: str = Field(min_length=1)
    invoice_number: str = Field(min_length=1)

    subtotal: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    vat: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    total: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )


class InvoiceValidationResult(BaseModel):
    invoice_number: str
    vendor: str
    is_valid: bool
    expected_total: Decimal
    declared_total: Decimal
    errors: list[str]

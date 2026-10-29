
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RawInvoiceFields(BaseModel):
    """Raw fields returned by the extraction model."""

    vendor: str | None
    invoice_number: str | None
    invoice_date: str | None

    subtotal: str | None
    vat: str | None
    total: str | None

    currency: str | None


class ExtractedInvoice(BaseModel):
    """Normalized invoice fields."""

    model_config = ConfigDict(
        extra="forbid",
    )

    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None

    subtotal: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    vat: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    total: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    currency: Literal["EUR"] | None = None


class ExtractionRequest(BaseModel):
    markdown: str = Field(
        min_length=1,
        max_length=30000,
    )
    method: Literal["regex", "llm"] = "regex"


class ExtractionResult(BaseModel):
    status: Literal[
        "validated",
        "review_required",
    ]
    method: Literal["regex", "llm"]
    invoice: ExtractedInvoice
    errors: list[str]

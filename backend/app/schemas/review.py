
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.extraction import ExtractionRequest


class CreateReviewRequest(ExtractionRequest):
    pass


class ReviewCorrection(BaseModel):
    fields: dict[
        Literal[
            "vendor",
            "invoice_number",
            "invoice_date",
            "subtotal",
            "vat",
            "total",
            "currency",
        ],
        str | None,
    ] = Field(min_length=1)


class ReviewDecision(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=128,
    )
    reason: str = Field(
        default="",
        max_length=1000,
    )

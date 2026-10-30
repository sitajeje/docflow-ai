
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class InvoiceReview(Base):
    __tablename__ = "invoice_reviews"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    source_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    source_markdown: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    raw_fields: Mapped[dict] = mapped_column(JSON)
    normalized_fields: Mapped[dict] = mapped_column(JSON)
    field_errors: Mapped[dict] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending_review",
        nullable=False,
    )

    reviewer: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_hash",
            "method",
            name="uq_review_source_method",
        ),
    )


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    review_id: Mapped[str] = mapped_column(
        ForeignKey("invoice_reviews.id"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    actor: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

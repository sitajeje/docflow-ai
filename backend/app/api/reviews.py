import hashlib
import hmac
import os
import httpx
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import InvoiceReview, ReviewEvent
from backend.app.db.session import get_db
from backend.app.schemas.review import (
    CreateReviewRequest,
    ReviewCorrection,
    ReviewDecision,
)
from backend.app.schemas.extraction import RawInvoiceFields
from backend.app.services.regex_extractor import extract_invoice_regex
from backend.app.services.llm_extractor import (
    LLMExtractionError,
    extract_invoice_llm,
)
from backend.app.services.review_validation import (
    normalize_with_errors,
)

load_dotenv()

router = APIRouter(
    prefix="/review-items",
    tags=["Review Items"],
)


def verify_key(
    provided: str | None,
    env_name: str,
) -> None:
    expected = os.getenv(env_name)

    if not expected or not provided or not hmac.compare_digest(
        provided, expected
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    verify_key(x_api_key, "DOCFLOW_API_KEY")


def require_reviewer_key(
    x_reviewer_key: str | None = Header(default=None),
) -> None:
    verify_key(x_reviewer_key, "DOCFLOW_REVIEWER_KEY")


def get_review_or_404(
    review_id: str,
    db: Session,
) -> InvoiceReview:
    review = db.get(InvoiceReview, review_id)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review item not found.",
        )

    return review


def serialize_review(review: InvoiceReview) -> dict:
    return {
        "id": review.id,
        "status": review.status,
        "method": review.method,
        "raw_fields": review.raw_fields,
        "normalized_fields": review.normalized_fields,
        "field_errors": review.field_errors,
        "reviewer": review.reviewer,
        "created_at": review.created_at.isoformat(),
        "reviewed_at": (
            review.reviewed_at.isoformat()
            if review.reviewed_at
            else None
        ),
    }


def record_event(
    db: Session,
    review_id: str,
    action: str,
    actor: str,
    details: dict,
) -> None:
    db.add(
        ReviewEvent(
            review_id=review_id,
            action=action,
            actor=actor,
            details=details,
        )
    )
    
@router.post("", dependencies=[Depends(require_api_key)])
def create_review(
    request: CreateReviewRequest,
    db: Session = Depends(get_db),
):
    source_hash = hashlib.sha256(
        request.markdown.encode("utf-8")
    ).hexdigest()

    existing = db.scalar(
        select(InvoiceReview).where(
            InvoiceReview.source_hash == source_hash,
            InvoiceReview.method == request.method,
        )
    )

    if existing:
        return serialize_review(existing)

    try:
        if request.method == "regex":
            raw = extract_invoice_regex(request.markdown)
        else:
            raw = extract_invoice_llm(request.markdown)
    except LLMExtractionError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    invoice, errors = normalize_with_errors(raw)

    review = InvoiceReview(
        source_hash=source_hash,
        method=request.method,
        source_markdown=request.markdown,
        raw_fields=raw.model_dump(mode="json"),
        normalized_fields=invoice.model_dump(mode="json"),
        field_errors=errors,
        status="pending_review",
    )

    db.add(review)
    db.flush()

    record_event(
        db,
        review.id,
        "created",
        "system",
        {"method": request.method},
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(InvoiceReview).where(
                InvoiceReview.source_hash == source_hash,
                InvoiceReview.method == request.method,
            )
        )
        if existing is None:
            raise
        return serialize_review(existing)

    db.refresh(review)
    return serialize_review(review)


@router.get(
    "/{review_id}",
    dependencies=[Depends(require_api_key)],
)
def get_review(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = get_review_or_404(review_id, db)
    return serialize_review(review)


@router.patch(
    "/{review_id}/fields",
    dependencies=[Depends(require_reviewer_key)],
)
def correct_review(
    review_id: str,
    request: ReviewCorrection,
    db: Session = Depends(get_db),
):
    review = get_review_or_404(review_id, db)

    if review.status != "pending_review":
        raise HTTPException(
            status_code=409,
            detail="Review is already finalized.",
        )

    before = dict(review.normalized_fields)

    # Start from the current corrected values
    updated = dict(before)
    updated.update(request.fields)

    raw = RawInvoiceFields.model_validate(updated)
    invoice, errors = normalize_with_errors(raw)

    review.normalized_fields = invoice.model_dump(mode="json")
    review.field_errors = errors

    record_event(
        db,
        review.id,
        "corrected",
        "local_reviewer",
        {
            "changed_fields": list(request.fields.keys()),
            "before": before,
            "after": review.normalized_fields,
        },
    )

    db.commit()
    db.refresh(review)

    return serialize_review(review)

@router.post(
    "/{review_id}/approve",
    dependencies=[Depends(require_reviewer_key)],
)
def approve_review(
    review_id: str,
    decision: ReviewDecision,
    db: Session = Depends(get_db),
):
    review = db.scalar(
        select(InvoiceReview)
        .where(InvoiceReview.id == review_id)
        .with_for_update()
    )

    if review is None:
        raise HTTPException(404, "Review item not found.")

    if review.status != "pending_review":
        raise HTTPException(409, "Review already finalized.")

    if review.field_errors:
        raise HTTPException(
            status_code=409,
            detail="Resolve validation errors before approval.",
        )

    review.status = "approved"
    review.reviewer = decision.reviewer
    review.reviewed_at = datetime.now(timezone.utc)

    record_event(
        db,
        review.id,
        "approved",
        decision.reviewer,
        {"reason": decision.reason},
    )

    db.commit()
    db.refresh(review)

    return serialize_review(review)


@router.post(
    "/{review_id}/reject",
    dependencies=[Depends(require_reviewer_key)],
)
def reject_review(
    review_id: str,
    decision: ReviewDecision,
    db: Session = Depends(get_db),
):
    review = db.scalar(
        select(InvoiceReview)
        .where(InvoiceReview.id == review_id)
        .with_for_update()
    )

    if review is None:
        raise HTTPException(404, "Review item not found.")

    if review.status != "pending_review":
        raise HTTPException(409, "Review already finalized.")

    if not decision.reason.strip():
        raise HTTPException(
            status_code=422,
            detail="A rejection reason is required.",
        )

    review.status = "rejected"
    review.reviewer = decision.reviewer
    review.reviewed_at = datetime.now(timezone.utc)

    record_event(
        db,
        review.id,
        "rejected",
        decision.reviewer,
        {"reason": decision.reason},
    )

    db.commit()
    db.refresh(review)

    return serialize_review(review)


@router.get(
    "/{review_id}/events",
    dependencies=[Depends(require_api_key)],
)
def get_review_events(
    review_id: str,
    db: Session = Depends(get_db),
):
    get_review_or_404(review_id, db)

    events = db.scalars(
        select(ReviewEvent)
        .where(ReviewEvent.review_id == review_id)
        .order_by(ReviewEvent.created_at, ReviewEvent.id)
    ).all()

    return [
        {
            "action": event.action,
            "actor": event.actor,
            "details": event.details,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]

@router.post(
    "/{review_id}/notify",
    dependencies=[Depends(require_api_key)],
)
def notify_reviewer(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = get_review_or_404(review_id, db)

    if review.status != "pending_review":
        raise HTTPException(
            status_code=409,
            detail="Only pending reviews can be notified.",
        )

    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    webhook_token = os.getenv("N8N_WEBHOOK_TOKEN")

    if not webhook_url or not webhook_token:
        raise HTTPException(
            status_code=503,
            detail="Notification service is not configured.",
        )

    try:
        response = httpx.post(
            webhook_url,
            headers={
                "X-Webhook-Token": webhook_token,
            },
            json={
                "event": "invoice.review_requested",
                "review_id": review.id,
                "status": review.status,
                "has_errors": bool(review.field_errors),
            },
            timeout=10.0,
        )
        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Notification delivery failed.",
        ) from exc

    return {
        "review_id": review.id,
        "notification": "accepted_by_webhook",
    }

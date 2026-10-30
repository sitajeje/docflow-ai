
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.models import Base
from backend.app.db.session import get_db


SAMPLE_MARKDOWN = """
FACTURE N° INV-2026-001
Fournisseur : Demo Consulting SAS
Date : 27/10/2026
Total HT : 100,00 €
TVA 20 % : 20,00 €
Total TTC : 130,00 €
"""

API_HEADERS = {
    "x-api-key": "test-api-key",
}

REVIEWER_HEADERS = {
    "x-reviewer-key": "test-reviewer-key",
}


@pytest.fixture
def client(monkeypatch):
    # Configure test-only API credentials
    monkeypatch.setenv(
        "DOCFLOW_API_KEY",
        "test-api-key",
    )
    monkeypatch.setenv(
        "DOCFLOW_REVIEWER_KEY",
        "test-reviewer-key",
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def create_sample_review(client):
    response = client.post(
        "/review-items",
        headers=API_HEADERS,
        json={
            "method": "regex",
            "markdown": SAMPLE_MARKDOWN,
        },
    )

    assert response.status_code == 200
    return response.json()


def test_create_review(client):
    data = create_sample_review(client)

    assert data["status"] == "pending_review"
    assert "business_rules" in data["field_errors"]


def test_review_is_idempotent(client):
    first = create_sample_review(client)
    second = create_sample_review(client)

    assert first["id"] == second["id"]


def test_cannot_approve_invalid_invoice(client):
    review = create_sample_review(client)

    response = client.post(
        f"/review-items/{review['id']}/approve",
        headers=REVIEWER_HEADERS,
        json={
            "reviewer": "test_accountant",
        },
    )

    assert response.status_code == 409


def test_correct_then_approve(client):
    review = create_sample_review(client)
    review_id = review["id"]

    correction = client.patch(
        f"/review-items/{review_id}/fields",
        headers=REVIEWER_HEADERS,
        json={
            "fields": {
                "total": "120.00",
            },
        },
    )

    assert correction.status_code == 200
    assert correction.json()["field_errors"] == {}

    approval = client.post(
        f"/review-items/{review_id}/approve",
        headers=REVIEWER_HEADERS,
        json={
            "reviewer": "test_accountant",
            "reason": "Verified against source",
        },
    )

    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"


def test_audit_history(client):
    review = create_sample_review(client)

    response = client.get(
        f"/review-items/{review['id']}/events",
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()[0]["action"] == "created"

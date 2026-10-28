
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_parser import (
    DocumentParsingError,
)

client = TestClient(app)

SAMPLE_PDF = b"%PDF-1.4\nmock test content"


def test_parse_pdf_success():
    # Replace the real parser with a mock result
    with patch(
        "backend.app.api.documents.parse_pdf",
        return_value="# FACTURE\nTotal TTC: 120 EUR",
    ) as mock_parser:

        response = client.post(
            "/documents/parse",
            files={
                "file": (
                    "invoice.pdf",
                    SAMPLE_PDF,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "parsed"
    assert "FACTURE" in response.json()["text"]
    mock_parser.assert_called_once()


def test_reject_non_pdf():
    response = client.post(
        "/documents/parse",
        files={
            "file": (
                "notes.txt",
                b"Hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_reject_invalid_pdf_signature():
    response = client.post(
        "/documents/parse",
        files={
            "file": (
                "fake.pdf",
                b"This is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 415


def test_parser_failure():
    with patch(
        "backend.app.api.documents.parse_pdf",
        side_effect=DocumentParsingError(
            "Document parsing failed."
        ),
    ):
        response = client.post(
            "/documents/parse",
            files={
                "file": (
                    "broken.pdf",
                    SAMPLE_PDF,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 422
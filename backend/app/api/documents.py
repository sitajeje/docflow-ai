
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, HTTPException, UploadFile

from backend.app.schemas.document import DocumentParseResult
from backend.app.services.document_parser import (
    DocumentParsingError,
    parse_pdf,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


@router.post(
    "/parse",
    response_model=DocumentParseResult,
)
def parse_document(
    file: UploadFile,
) -> DocumentParseResult:

    filename = Path(file.filename or "").name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are supported.",
        )

    temp_path = None

    try:
        with NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            total_size = 0
            header = b""

            while True:
                chunk = file.file.read(CHUNK_SIZE)

                if not chunk:
                    break

                if not header:
                    header = chunk[:5]

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds 10 MB.",
                    )

                temp_file.write(chunk)

        if header != b"%PDF-":
            raise HTTPException(
                status_code=415,
                detail="Invalid PDF file signature.",
            )

        markdown = parse_pdf(temp_path)

        return DocumentParseResult(
            filename=filename,
            status="parsed",
            content_type="application/pdf",
            text=markdown,
            character_count=len(markdown),
        )

    except DocumentParsingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        file.file.close()

        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

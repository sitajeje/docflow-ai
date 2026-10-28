
from pathlib import Path

from docling.document_converter import DocumentConverter


class DocumentParsingError(Exception):
    pass


def parse_pdf(file_path: Path) -> str:
    # Verify that the input file exists
    if not file_path.is_file():
        raise DocumentParsingError(
            "PDF file does not exist."
        )

    try:
        converter = DocumentConverter()

        # Convert PDF into a structured document
        result = converter.convert(str(file_path))

        # Export structured content as Markdown
        markdown = result.document.export_to_markdown()

        if not markdown.strip():
            raise DocumentParsingError(
                "No text could be extracted."
            )

        return markdown

    except DocumentParsingError:
        raise

    except Exception as exc:
        raise DocumentParsingError(
            "Document parsing failed."
        ) from exc

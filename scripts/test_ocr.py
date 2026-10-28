
from pathlib import Path
import sys

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    OcrMacOptions,
    PdfPipelineOptions,
    OcrMode,
)


def main(file_path: Path):
    pipeline_options = PdfPipelineOptions(
        do_ocr=True,
    )

    pipeline_options.ocr_options = OcrMacOptions(
        mode=OcrMode.FULL_PAGE,
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            ),
        }
    )

    result = converter.convert(str(file_path))

    print(result.document.export_to_markdown())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m scripts.test_ocr <pdf-path>"
        )

    main(Path(sys.argv[1]))

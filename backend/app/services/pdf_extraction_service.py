from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when PDF text extraction fails."""


def extract_pdf_pages(file_path: str | Path) -> list[dict[str, str | int]]:
    """
    Extract text page by page.
    Each returned item contains:
    - page_number: original PDF page number (1-based)
    - text: extracted text from that page
    """
    path = Path(file_path)

    if not path.is_file():
        raise PDFExtractionError("The PDF file does not exist.")

    try:
        with pymupdf.open(path) as pdf:
            if pdf.is_encrypted:
                raise PDFExtractionError("Encrypted PDFs are not supported.")

            if pdf.page_count == 0:
                raise PDFExtractionError("The PDF contains no pages.")

            extracted_pages: list[dict[str, str | int]] = []

            for page_index, page in enumerate(pdf):
                raw_text = page.get_text("text")
                if not isinstance(raw_text, str):
                    raise PDFExtractionError(
                        "PDF text extraction returned an unexpected result."
                    )
                page_text = raw_text.strip()
                if page_text:
                    extracted_pages.append({
                        "page_number": page_index + 1,
                        "text": page_text,
                    })

            if not extracted_pages:
                raise PDFExtractionError(
                    "No extractable text was found in the PDF. "
                    "It may contain scanned images rather than text."
                )

            return extracted_pages

    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(
            "The PDF could not be read or processed."
        ) from exc


def extract_pdf_text(file_path: str | Path) -> str:
    """Extract text from a PDF file and return it as a single string."""
    pages = extract_pdf_pages(file_path)
    return "\n\n".join(str(p["text"]) for p in pages).strip()

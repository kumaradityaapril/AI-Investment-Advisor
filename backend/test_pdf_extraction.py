from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf

from app.services.pdf_extraction_service import (
    PDFExtractionError,
    extract_pdf_text,
)


def main():
    with TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "financial_report.pdf"

        # Generate a small PDF containing known financial text.
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text(
                (72, 72),
                "Annual Financial Report 2026\n"
                "Revenue: INR 500000\n"
                "Net Profit: INR 75000",
            )
            pdf.save(pdf_path)

        # Test successful extraction.
        extracted_text = extract_pdf_text(pdf_path)
        assert "Annual Financial Report 2026" in extracted_text
        assert "Revenue: INR 500000" in extracted_text
        assert "Net Profit: INR 75000" in extracted_text
        print("PASS: PDF text extracted successfully")
        print("Extracted text:")
        print(extracted_text)

        # Test missing file handling
        missing_path = Path(temp_dir) / "non_existent.pdf"
        try:
            extract_pdf_text(missing_path)
            assert False, "Expected PDFExtractionError for missing file"
        except PDFExtractionError as exc:
            assert "The PDF file does not exist." in str(exc)
            print("PASS: Missing file handled correctly")

        # Test an empty PDF with no pages.
        empty_pdf_path = Path(temp_dir) / "empty.pdf"
        empty_pdf_path.write_bytes(
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
            b"xref\n0 3\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n110\n%%EOF\n"
        )
        try:
            extract_pdf_text(empty_pdf_path)
            raise AssertionError("Expected an error for a PDF with no pages")
        except PDFExtractionError as exc:
            assert "no pages" in str(exc).lower()
            print("PASS: Empty PDF handled correctly")

        # Test a PDF containing a blank page.
        blank_pdf_path = Path(temp_dir) / "blank.pdf"
        with pymupdf.open() as blank_pdf:
            blank_pdf.new_page()
            blank_pdf.save(blank_pdf_path)
        try:
            extract_pdf_text(blank_pdf_path)
            raise AssertionError("Expected an error for a PDF with no text")
        except PDFExtractionError as exc:
            assert "no extractable text" in str(exc).lower()
            print("PASS: Blank PDF handled correctly")

        # Test a file that is not actually a PDF.
        invalid_pdf_path = Path(temp_dir) / "invalid.pdf"
        invalid_pdf_path.write_text(
            "This is not a PDF file.",
            encoding="utf-8",
        )
        try:
            extract_pdf_text(invalid_pdf_path)
            raise AssertionError("Expected an error for an invalid PDF")
        except PDFExtractionError as exc:
            print("PASS: Invalid PDF handled correctly")


if __name__ == "__main__":
    main()

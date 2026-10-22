
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document


CHUNK_SIZE = 1024 * 1024  # Read at most 1 MiB at a time.
PDF_CONTENT_TYPE = "application/pdf"


def _upload_directory() -> Path:
    """Resolve and create the configured upload directory."""
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parents[2] / directory

    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_document(
    db: Session,
    user_id: int,
    file: UploadFile,
) -> Document:
    """Validate, store, and register an uploaded PDF."""
    original_filename = Path(file.filename or "").name.strip()

    if not original_filename or len(original_filename) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid filename of at most 255 characters is required.",
        )

    if Path(original_filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    if file.content_type != PDF_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must have content type application/pdf.",
        )

    stored_filename = f"{uuid4().hex}.pdf"
    destination = _upload_directory() / stored_filename
    total_bytes = 0
    header = b""

    try:
        with destination.open("xb") as output:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=("The PDF exceeds the maximum allowed size of " f"{settings.max_upload_size_bytes / (1024 * 1024):g} MiB."),
                    )

                if len(header) < 5:
                    header += chunk[: 5 - len(header)]

                output.write(chunk)

        # Check the PDF signature, not just the extension and MIME type.
        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="The uploaded file does not have a valid PDF signature.",
            )

        document = Document(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=PDF_CONTENT_TYPE,
            file_size_bytes=total_bytes,
            status="uploaded",
        )

        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    finally:
        file.file.close()

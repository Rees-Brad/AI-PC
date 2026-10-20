"""Extract selectable text from PDF starting material."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

DEFAULT_MAX_BYTES = 500 * 1024


class PdfTextError(ValueError):
    """A problem with the PDF that the DM can act on."""


def extract_pdf_text(path: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    """Return the PDF's selectable text, or raise ValueError with a reason the DM can act on."""
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"{path} does not exist.")
    limit_kb = max_bytes // 1024
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError(f"{path.name} is not a valid PDF.")

    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PdfTextError("Password-protected PDFs are not supported.")
        pages_text = []
        total_bytes = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            total_bytes += len(page_text.encode("utf-8"))
            if total_bytes > max_bytes:
                raise PdfTextError(f"Extracted PDF text exceeds the {limit_kb} KB limit.")
            if page_text.strip():
                pages_text.append(page_text)
    except PdfTextError:
        raise
    except Exception as error:
        raise ValueError(
            "Could not read this PDF. Make sure it is valid and not damaged."
        ) from error

    extracted_text = "\n\n".join(pages_text).strip()
    if not extracted_text:
        raise ValueError(
            "No selectable text was found in this PDF. Scanned PDFs need OCR before they "
            "can be used."
        )
    return extracted_text

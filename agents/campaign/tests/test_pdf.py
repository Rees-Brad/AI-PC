from __future__ import annotations

from pathlib import Path

import pytest

from ai_campaign.pdf import extract_pdf_text


def make_pdf(text: str) -> bytes:
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    stream = (
        b"<< /Length "
        + str(len(content)).encode("ascii")
        + b" >>\nstream\n"
        + content
        + b"\nendstream"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        stream,
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, item in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii") + item + b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return bytes(pdf)


def test_extracts_selectable_text(tmp_path: Path) -> None:
    path = tmp_path / "notes.pdf"
    path.write_bytes(make_pdf("A drowned kingdom rises"))
    assert extract_pdf_text(path) == "A drowned kingdom rises"


@pytest.mark.parametrize(
    "content, message",
    [
        (make_pdf(""), "Scanned PDFs need OCR"),
        (b"not a pdf", "not a valid PDF"),
        (b"%PDF-1.4 broken", "Could not read this PDF"),
    ],
)
def test_reports_unusable_pdfs(tmp_path: Path, content: bytes, message: str) -> None:
    path = tmp_path / "bad.pdf"
    path.write_bytes(content)
    with pytest.raises(ValueError, match=message):
        extract_pdf_text(path)


def test_enforces_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "long.pdf"
    path.write_bytes(make_pdf("x" * 2048))
    with pytest.raises(ValueError, match="exceeds the 1 KB limit"):
        extract_pdf_text(path, max_bytes=1024)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        extract_pdf_text(tmp_path / "nope.pdf")

import pytest
from fastapi import HTTPException

from utils.sql_safety import validate_file_mime_and_signature


@pytest.mark.parametrize(
    "name,content_type,content",
    [
        ("doc.pdf", "application/pdf", b"%PDF-1.7 test"),
        ("img.png", "image/png", b"\x89PNG\r\n\x1a\nrest"),
        ("photo.jpg", "image/jpeg", b"\xff\xd8\xff\xe0rest"),
        ("sheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"PK\x03\x04rest"),
    ],
)
def test_validate_file_mime_and_signature_accepts_valid_files(name, content_type, content):
    ext = validate_file_mime_and_signature(name, content_type, content, "file")
    assert ext.startswith(".")


def test_validate_file_mime_and_signature_rejects_mime_mismatch():
    with pytest.raises(HTTPException) as exc:
        validate_file_mime_and_signature("doc.pdf", "image/png", b"%PDF-1.7", "file")
    assert exc.value.status_code == 400


def test_validate_file_mime_and_signature_rejects_signature_mismatch():
    with pytest.raises(HTTPException) as exc:
        validate_file_mime_and_signature("doc.pdf", "application/pdf", b"NOTPDF", "file")
    assert exc.value.status_code == 400


def test_validate_file_mime_and_signature_rejects_text_with_null_byte():
    with pytest.raises(HTTPException) as exc:
        validate_file_mime_and_signature("data.csv", "text/csv", b"a,b\x00c", "file")
    assert exc.value.status_code == 400

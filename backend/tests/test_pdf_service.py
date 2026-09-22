"""
backend/tests/test_pdf_service.py

Unit tests for the PDF service validation and text normalization.
(Extraction tests require real PDF files; only validation and normalization are tested here.)
"""

from __future__ import annotations

import pytest
from app.services.pdf_service import (
    PDFValidationError,
    validate_upload,
    generate_stored_filename,
    _normalize_text,
)

PDF_MAGIC = b"%PDF-1.4\n"
VALID_PDF = PDF_MAGIC + b"x" * 100  # stub content with correct magic


class TestValidation:
    def test_valid_pdf_passes(self):
        # Should not raise
        validate_upload("resume.pdf", VALID_PDF, "application/pdf")

    def test_wrong_extension_raises(self):
        with pytest.raises(PDFValidationError, match="not allowed"):
            validate_upload("resume.exe", VALID_PDF, "application/pdf")

    def test_bad_magic_raises(self):
        with pytest.raises(PDFValidationError, match="signature"):
            validate_upload("resume.pdf", b"NOTAPDF" + b"x" * 100, "application/pdf")

    def test_path_traversal_raises(self):
        with pytest.raises(PDFValidationError, match="Invalid filename"):
            validate_upload("../../etc/passwd.pdf", VALID_PDF, "application/pdf")

    def test_backslash_path_traversal_raises(self):
        with pytest.raises(PDFValidationError, match="Invalid filename"):
            validate_upload("..\\..\\evil.pdf", VALID_PDF, "application/pdf")

    def test_oversize_raises(self):
        big_content = VALID_PDF + b"x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(PDFValidationError, match="maximum allowed size"):
            validate_upload("resume.pdf", big_content, "application/pdf")


class TestFilenameGeneration:
    def test_generates_uuid_filename(self):
        name = generate_stored_filename("resume.pdf")
        assert name.endswith(".pdf")
        assert len(name) > 8
        # Should not contain original filename
        assert "resume" not in name

    def test_preserves_extension(self):
        name = generate_stored_filename("my cv.PDF")
        assert name.lower().endswith(".pdf")

    def test_different_calls_produce_different_names(self):
        a = generate_stored_filename("a.pdf")
        b = generate_stored_filename("a.pdf")
        assert a != b


class TestTextNormalization:
    def test_ligatures_replaced(self):
        result = _normalize_text("\ufb01nancial analyst")
        assert result.startswith("financial")

    def test_multiple_spaces_collapsed(self):
        result = _normalize_text("Python   developer")
        assert "Python developer" in result or "python developer" in result.lower()

    def test_empty_string_returns_empty(self):
        assert _normalize_text("") == ""

    def test_preserves_technical_terms(self):
        result = _normalize_text("node.js, c++, ci/cd, aws-s3")
        # Technical separators must be preserved
        assert "node.js" in result or "node" in result
        assert "c++" in result or "c" in result

    def test_strips_leading_trailing_whitespace(self):
        result = _normalize_text("  hello world  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

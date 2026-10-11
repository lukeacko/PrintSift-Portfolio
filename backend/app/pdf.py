from io import BytesIO

from pypdf import PdfReader


MAX_PDF_PAGES = 500
MAX_EXTRACTED_TEXT_CHARACTERS = 2_000_000


class PDFValidationError(ValueError):
    """Raised when an uploaded file is not a usable PDF."""


class PDFEncryptedError(PDFValidationError):
    """Raised when a PDF requires a password."""


class PDFTooManyPagesError(PDFValidationError):
    """Raised when a PDF exceeds the configured page limit."""


class PDFTextLimitError(PDFValidationError):
    """Raised when extracted PDF text is unexpectedly large."""


def has_pdf_signature(contents: bytes) -> bool:
    if not contents:
        return False
    return b"%PDF-" in contents[:1024]


def extract_pdf_pages(
    contents: bytes,
    *,
    max_pages: int = MAX_PDF_PAGES,
    max_extracted_characters: int = MAX_EXTRACTED_TEXT_CHARACTERS,
) -> list[str]:
    if not contents:
        raise PDFValidationError("The uploaded PDF is empty.")

    if not has_pdf_signature(contents):
        raise PDFValidationError(
            "The uploaded file does not contain a valid PDF header."
        )

    try:
        reader = PdfReader(BytesIO(contents), strict=False)
    except Exception as exc:
        raise PDFValidationError(
            "The uploaded file could not be parsed as a PDF."
        ) from exc

    if reader.is_encrypted:
        try:
            decrypt_result = reader.decrypt("")
        except Exception as exc:
            raise PDFEncryptedError(
                "Password-protected PDFs are not currently supported."
            ) from exc

        if not decrypt_result:
            raise PDFEncryptedError(
                "Password-protected PDFs are not currently supported."
            )

    try:
        page_count = len(reader.pages)
    except Exception as exc:
        raise PDFValidationError(
            "The PDF page structure could not be read."
        ) from exc

    if page_count == 0:
        raise PDFValidationError("The uploaded PDF does not contain any pages.")

    if page_count > max_pages:
        raise PDFTooManyPagesError(f"PDFs are limited to {max_pages} pages.")

    pages: list[str] = []
    total_characters = 0

    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise PDFValidationError(
                "Text could not be extracted from one or more PDF pages."
            ) from exc

        total_characters += len(text)
        if total_characters > max_extracted_characters:
            raise PDFTextLimitError(
                "The PDF contains too much extractable text to process safely."
            )
        pages.append(text)

    return pages


def format_pages_for_ai(pages: list[str]) -> str:
    blocks = []
    for page_number, text in enumerate(pages, start=1):
        blocks.append(f"=== PAGE {page_number} ===\n{text}")
    return "\n\n".join(blocks)


def requires_ocr(pages: list[str]) -> bool:
    total_characters = sum(len(page.strip()) for page in pages)
    return total_characters < 500

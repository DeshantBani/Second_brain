"""Text extraction for uploaded documents - PDF (text layer), DOCX, and plain
text/markdown. Deliberately no OCR (per the build plan's original scope: "support
clean digital text (docx, pdf-with-text-layer, email) first; add an OCR pass as a
discrete, swappable ingestion step later") - a scanned/image-only PDF will extract to
empty text, and callers must treat that as an error, not silently accept a blank
document.

For PDFs, page breaks are preserved as "## PAGE N" markers matching the convention
services/ingestion.py::parse_page_map already expects, so an uploaded PDF fed into
matter/document intake gets real per-page source-linking, not just one undifferentiated
blob of text. DOCX has no reliable page concept via python-docx (page breaks are a
rendering-time detail, not stored per-paragraph), so it's treated as a single page -
the same fallback parse_page_map already applies to any unmarked text.
"""
import io

from docx import Document as DocxDocument
from pypdf import PdfReader

MAX_EXTRACTED_CHARS = 200_000


class UnsupportedFileType(Exception):
    pass


class NoExtractableText(Exception):
    pass


def _extract_pdf(content: bytes, add_page_markers: bool) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = []
    any_real_text = False
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            any_real_text = True
        if add_page_markers:
            pages.append(f"## PAGE {i}\n{text}")
        elif text:
            pages.append(text)
    # A page-marker-only result (every page's text was empty - e.g. a scanned/
    # image-only PDF) must still come back empty, not a shell of bare markers that
    # would pass the caller's blank-text check and silently pretend to have extracted
    # something.
    return "\n\n".join(pages) if any_real_text else ""


def _extract_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_upload(filename: str, content: bytes, content_type: str, add_page_markers: bool = True) -> str:
    """Returns extracted text, truncated to MAX_EXTRACTED_CHARS. Raises
    UnsupportedFileType for a format we don't handle, NoExtractableText if extraction
    produced nothing usable (e.g. a scanned/image-only PDF)."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf" or content_type == "application/pdf":
        text = _extract_pdf(content, add_page_markers)
    elif ext == "docx" or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = _extract_docx(content)
    elif ext in ("txt", "md") or content_type.startswith("text/"):
        text = content.decode("utf-8", errors="replace")
    else:
        raise UnsupportedFileType(f"Unsupported file type '{filename}' - upload a PDF, DOCX, TXT, or MD file.")

    text = text.strip()
    if not text:
        raise NoExtractableText(
            "No extractable text was found in this file. If it's a scanned/image-only PDF, "
            "OCR isn't supported yet - paste the text directly instead."
        )
    return text[:MAX_EXTRACTED_CHARS]

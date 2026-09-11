from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.deps import CurrentUser, get_current_user
from app.services.text_extraction import NoExtractableText, UnsupportedFileType, extract_text_from_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15MB


@router.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    add_page_markers: bool = Form(True),
    user: CurrentUser = Depends(get_current_user),
):
    """Stateless utility, shared by every free-text intake surface in the app (case
    brief, new-matter/add-document raw text, proofreading draft text): pulls text out
    of an uploaded PDF/DOCX/TXT/MD so a lawyer can upload a document instead of pasting
    it. No OCR - a scanned/image-only PDF raises a clear error rather than silently
    returning nothing."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 15MB)")

    try:
        text = extract_text_from_upload(file.filename or "upload", content, file.content_type or "", add_page_markers)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except NoExtractableText as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - a malformed file should be a clean 422, not a 500
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Could not extract text from this file: {exc}")

    return {"filename": file.filename, "text": text, "truncated": len(text) >= 200_000}

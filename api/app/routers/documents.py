from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.document import Document
from app.models.matter import Matter
from app.schemas.document import IngestDocumentRequest, IngestDocumentResponse
from app.services.ingestion import build_matter_fingerprint, ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestDocumentResponse)
async def ingest(payload: IngestDocumentRequest, db: Session = Depends(get_db)):
    matter = db.get(Matter, payload.matter_id)
    if matter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found or not accessible")

    doc = await ingest_document(
        db, payload.matter_id, payload.title, payload.doc_type, payload.confidentiality_tier, payload.text
    )

    all_docs = db.query(Document).filter(Document.matter_id == payload.matter_id).all()
    combined_text = "\n\n".join(d.extracted_text for d in all_docs)
    fingerprint, degraded = await build_matter_fingerprint(db, payload.matter_id, combined_text)

    return IngestDocumentResponse(
        document_id=str(doc.id),
        fingerprint_id=str(fingerprint.id) if fingerprint else None,
        degraded_mode=degraded,
    )

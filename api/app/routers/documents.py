from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.document import Document
from app.models.matter import Matter
from app.schemas.document import IngestDocumentRequest, IngestDocumentResponse, LinkedCitationOut
from app.services.ingestion import build_matter_fingerprint, ingest_document
from app.services.matter_intake import extract_and_link_citations

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestDocumentResponse)
async def ingest(payload: IngestDocumentRequest, db: Session = Depends(get_db)):
    """Add a document to an EXISTING matter (the RLS-scoped `db` here already proves
    the caller has access to it). Re-fingerprints the whole matter from all of its
    documents combined, and scans just the new document for case-law citations - see
    services/matter_intake.py."""
    matter = db.get(Matter, payload.matter_id)
    if matter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found or not accessible")

    doc = await ingest_document(
        db, payload.matter_id, payload.title, payload.doc_type, payload.confidentiality_tier, payload.text
    )

    all_docs = db.query(Document).filter(Document.matter_id == payload.matter_id).all()
    combined_text = "\n\n".join(d.extracted_text for d in all_docs)
    fingerprint, degraded = await build_matter_fingerprint(db, payload.matter_id, combined_text)

    citations_linked = []
    if not degraded:
        citations_linked = await extract_and_link_citations(db, payload.matter_id, doc)

    return IngestDocumentResponse(
        document_id=str(doc.id),
        fingerprint_id=str(fingerprint.id) if fingerprint else None,
        degraded_mode=degraded,
        citations_linked=[LinkedCitationOut(**c) for c in citations_linked],
    )

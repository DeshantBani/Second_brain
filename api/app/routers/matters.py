from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_current_user, get_db
from app.models.authority import Authority
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.models.matter import Matter
from app.models.matter_authority import MatterAuthority
from app.schemas.document import CreateMatterRequest, CreateMatterResponse, LinkedCitationOut
from app.schemas.matter import AuthorityRef, DocumentDetail, DocumentSummary, FingerprintOut, MatterDetail, MatterSummary
from app.services.matter_intake import ingest_new_matter

router = APIRouter(prefix="/matters", tags=["matters"])


@router.get("", response_model=list[MatterSummary])
def list_matters(db: Session = Depends(get_db)):
    # RLS on `matters` already limits this to what the current user has an AccessGrant for.
    matters = db.execute(select(Matter).order_by(Matter.opened_date.desc().nulls_last())).scalars().all()
    return [MatterSummary.model_validate(m) for m in matters]


@router.post("", response_model=CreateMatterResponse)
async def create_matter(payload: CreateMatterRequest, user: CurrentUser = Depends(get_current_user)):
    """New-matter intake: creates the matter, ingests its first document, and runs the
    same AI fingerprinting + citation-extraction pipeline every matter in the archive
    goes through - see services/matter_intake.py for why this uses its own DB session
    rather than the usual RLS-scoped one."""
    if not payload.title.strip() or not payload.client_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title and client_name are required")
    if not payload.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="raw_text must not be empty")

    parsed_date: date | None = None
    if payload.opened_date:
        try:
            parsed_date = date.fromisoformat(payload.opened_date)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="opened_date must be an ISO date (YYYY-MM-DD)")

    result = await ingest_new_matter(
        user_id=user.id, title=payload.title, client_name=payload.client_name,
        doc_title=payload.doc_title, doc_type=payload.doc_type,
        confidentiality_tier=payload.confidentiality_tier, opened_date=parsed_date,
        raw_text=payload.raw_text,
    )
    return CreateMatterResponse(
        matter_id=result["matter_id"], document_id=result["document_id"], degraded_mode=result["degraded_mode"],
        jurisdiction=result["jurisdiction"], practice_area=result["practice_area"], matter_type=result["matter_type"],
        citations_linked=[LinkedCitationOut(**c) for c in result["citations_linked"]],
    )


@router.get("/{matter_id}", response_model=MatterDetail)
def get_matter(matter_id: str, db: Session = Depends(get_db)):
    matter = db.get(Matter, matter_id)
    if matter is None:
        # RLS makes an out-of-scope matter indistinguishable from a nonexistent one - by design.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

    documents = db.execute(select(Document).where(Document.matter_id == matter_id)).scalars().all()
    fp = db.execute(select(IssueFingerprint).where(IssueFingerprint.matter_id == matter_id)).scalar_one_or_none()
    auth_rows = db.execute(
        select(MatterAuthority, Authority).join(Authority, Authority.id == MatterAuthority.authority_id)
        .where(MatterAuthority.matter_id == matter_id)
    ).all()

    return MatterDetail(
        **MatterSummary.model_validate(matter).model_dump(),
        documents=[DocumentSummary.model_validate(d) for d in documents],
        authorities=[
            AuthorityRef(
                id=str(a.id), citation=a.citation, court=a.court, year=a.year,
                status=a.status, monitoring_status=a.monitoring_status,
                relied_upon_for=ma.relied_upon_for, cited_at_page=ma.cited_at_page, cited_at_paragraph=ma.cited_at_paragraph,
            )
            for ma, a in auth_rows
        ],
        fingerprint=FingerprintOut.model_validate(fp) if fp else None,
    )


@router.get("/{matter_id}/documents/{document_id}", response_model=DocumentDetail)
def get_document(matter_id: str, document_id: str, db: Session = Depends(get_db)):
    matter = db.get(Matter, matter_id)
    if matter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")
    doc = db.get(Document, document_id)
    if doc is None or str(doc.matter_id) != str(matter_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentDetail.model_validate(doc)

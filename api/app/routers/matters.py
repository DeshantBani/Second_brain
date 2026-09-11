from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.authority import Authority
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.models.matter import Matter
from app.models.matter_authority import MatterAuthority
from app.schemas.matter import AuthorityRef, DocumentDetail, DocumentSummary, FingerprintOut, MatterDetail, MatterSummary

router = APIRouter(prefix="/matters", tags=["matters"])


@router.get("", response_model=list[MatterSummary])
def list_matters(db: Session = Depends(get_db)):
    # RLS on `matters` already limits this to what the current user has an AccessGrant for.
    matters = db.execute(select(Matter).order_by(Matter.opened_date.desc().nulls_last())).scalars().all()
    return [MatterSummary.model_validate(m) for m in matters]


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

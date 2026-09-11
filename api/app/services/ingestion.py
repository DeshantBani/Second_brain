"""Ingestion for clean digital text only in this pass (docx/pdf-with-text-layer/email
extraction and OCR are a discrete, swappable future step - see build plan Section 2).

Fixture/seed documents are authored with a lightweight page marker convention so every
downstream agent can cite an exact, real page/paragraph:

    ## PAGE 1
    First paragraph of page 1.

    Second paragraph of page 1.
    ## PAGE 2
    First paragraph of page 2.

Real user-uploaded text that lacks page markers is treated as a single page whose
paragraphs are its blank-line-separated blocks.
"""
import re
import uuid

from sqlalchemy.orm import Session

from app.agents_sdk.fingerprint_agent import run_fingerprint_agent
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.services.embeddings import embed_text
from app.services.fingerprint_text import fingerprint_to_embedding_text
from app.services.storage import put_text

PAGE_MARKER_RE = re.compile(r"^##\s*PAGE\s+(\d+)\s*$", re.MULTILINE)


def parse_page_map(raw_text: str) -> list[dict]:
    markers = list(PAGE_MARKER_RE.finditer(raw_text))
    page_map: list[dict] = []

    if not markers:
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs, start=1):
            page_map.append({"page": 1, "paragraph": i, "text": para})
        return page_map

    for idx, marker in enumerate(markers):
        page_num = int(marker.group(1))
        start = marker.end()
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(raw_text)
        page_text = raw_text[start:end].strip()
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
        for para_idx, para in enumerate(paragraphs, start=1):
            page_map.append({"page": page_num, "paragraph": para_idx, "text": para})
    return page_map


async def ingest_document(
    db: Session,
    matter_id: str,
    title: str,
    doc_type: str,
    confidentiality_tier: str,
    raw_text: str,
) -> Document:
    page_map = parse_page_map(raw_text)
    storage_key = f"matters/{matter_id}/{uuid.uuid4()}.md"
    put_text(storage_key, raw_text)

    doc = Document(
        matter_id=matter_id,
        title=title,
        doc_type=doc_type,
        confidentiality_tier=confidentiality_tier,
        storage_key=storage_key,
        mime_type="text/markdown",
        extracted_text=raw_text,
        page_map=page_map,
    )
    db.add(doc)
    db.flush()
    return doc


async def build_matter_fingerprint(db: Session, matter_id: str, combined_text: str) -> tuple[IssueFingerprint | None, bool]:
    """One fingerprint per matter (data model constraint) - replaces any existing row
    for this matter. Returns (fingerprint_row_or_None, degraded_mode)."""
    from app.agents_sdk.client import AgentError

    try:
        fp = await run_fingerprint_agent(combined_text)
    except AgentError:
        return None, True

    embedding_text = fingerprint_to_embedding_text(fp)
    vector = embed_text(embedding_text)

    existing = db.query(IssueFingerprint).filter(
        IssueFingerprint.matter_id == matter_id, IssueFingerprint.is_ephemeral.is_(False)
    ).one_or_none()
    if existing:
        db.delete(existing)
        db.flush()

    row = IssueFingerprint(
        matter_id=matter_id,
        is_ephemeral=False,
        jurisdiction=fp.jurisdiction,
        practice_area=fp.practice_area,
        procedural_posture=fp.procedural_posture,
        factual_pattern={"text": fp.factual_pattern, "matter_type": fp.matter_type},
        contract_clauses={"clauses": [c.model_dump() for c in fp.contract_clauses]},
        clause_tags=fp.clause_tags,
        summary=fp.summary,
        embedding=vector,
    )
    db.add(row)
    db.flush()
    return row, vector is None

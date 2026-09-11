"""New-matter intake: the AI-aligned ingestion path requested for the Matters page.

Two entry points:
- `ingest_new_matter` - creates a brand new Matter (+ grants the creating user access
  to it) from a title/client name and one document's raw text, then runs the exact
  same fingerprint pipeline every matter in the archive already goes through
  (services/ingestion.py::build_matter_fingerprint) so the new matter's
  jurisdiction/practice_area/clause_tags land in the same controlled vocabulary
  (agents_sdk/tools.py::TAXONOMY) the retrieval funnel's structured filter depends on
  - "aligned with the current structure" means exactly this: the AI derives these
  fields the same way it does for every other matter, rather than a human guessing at
  values that might not match what the retrieval SQL filters on.
- `extract_and_link_citations` - runs the citation-extraction agent over one document
  and writes any verified citations as Authority/MatterAuthority rows, so the
  Authorities tab on the matter page populates automatically. Used by both
  `ingest_new_matter` (the new document) and routers/documents.py's existing
  "add a document to an existing matter" endpoint.

RLS note: creating a brand-new matter is a genuine chicken-and-egg problem for the
matters table's row-level-security policy - a matter can't have an AccessGrant before
it exists, and it can't be INSERTed under RLS without one already existing (WITH CHECK
falls back to the USING clause, which requires a pre-existing grant). So this module
uses OwnerSessionLocal (bypasses RLS) for the create path, exactly like db/seed/seed_data.py
already does - creating a matter and its first grant is a privileged operation, not a
per-row read/write. Adding a document to an EXISTING matter (extract_and_link_citations
called from routers/documents.py) has no such problem and uses the caller's normal
RLS-scoped session, since the matter is already accessible to that user.
"""
import json
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents_sdk.citation_extraction_agent import run_citation_extraction_agent
from app.agents_sdk.client import AgentError
from app.agents_sdk.text_match import fuzzy_contains
from app.config import get_settings
from app.db import OwnerSessionLocal
from app.models.access_grant import AccessGrant
from app.models.authority import Authority
from app.models.document import Document
from app.models.matter import Matter
from app.models.matter_authority import MatterAuthority
from app.reliability.factory import get_case_law_provider
from app.services.ingestion import build_matter_fingerprint, ingest_document

logger = logging.getLogger("second_brain.matter_intake")

settings = get_settings()


async def extract_and_link_citations(db: Session, matter_id: str, doc: Document) -> list[dict]:
    """Scan one document for case-law citations and write verified ones as
    Authority/MatterAuthority rows. Never trusts the extraction agent's citation
    status (there isn't one to trust - it doesn't report one); status always comes
    from get_case_law_provider(), exactly like the reliability agent."""
    if not doc.page_map:
        return []

    try:
        result = await run_citation_extraction_agent(doc.title, doc.page_map)
    except AgentError as exc:
        logger.warning("citation extraction unavailable, skipping: %s", exc)
        return []

    provider = get_case_law_provider()
    linked: list[dict] = []

    for candidate in result.citations:
        span = next(
            (p for p in doc.page_map if p.get("page") == candidate.page and p.get("paragraph") == candidate.paragraph),
            None,
        )
        if span is None or not fuzzy_contains(span.get("text", ""), candidate.quote):
            logger.warning("dropping unverifiable extracted citation '%s' - quote not found in document", candidate.citation)
            continue

        authority = db.execute(select(Authority).where(Authority.citation == candidate.citation)).scalar_one_or_none()
        is_new = authority is None
        if authority is None:
            status = provider.get_citation_status(candidate.citation)
            authority = Authority(
                citation=candidate.citation,
                court=candidate.court or "Unknown",
                year=candidate.year or 0,
                status=status.status,
                treatment_history=[e.model_dump(mode="json") for e in status.treatment_history],
                monitoring_status="checked_flagged" if status.treatment_history else "checked_clear",
                last_checked_at=datetime.now(timezone.utc),
                provider_source=settings.case_law_provider,
            )
            db.add(authority)
            db.flush()

        already_linked = db.execute(
            select(MatterAuthority).where(
                MatterAuthority.matter_id == matter_id, MatterAuthority.authority_id == authority.id,
                MatterAuthority.cited_in_document_id == doc.id, MatterAuthority.cited_at_page == candidate.page,
                MatterAuthority.cited_at_paragraph == candidate.paragraph,
            )
        ).scalar_one_or_none()
        if already_linked is None:
            db.add(MatterAuthority(
                matter_id=matter_id, authority_id=authority.id, cited_in_document_id=doc.id,
                cited_at_page=candidate.page, cited_at_paragraph=candidate.paragraph,
                relied_upon_for=candidate.relied_upon_for,
            ))

        linked.append({"citation": authority.citation, "status": authority.status, "is_new_authority": is_new})

    db.flush()
    return linked


async def ingest_new_matter(
    *, user_id: str, title: str, client_name: str, doc_title: str, doc_type: str,
    confidentiality_tier: str, opened_date: date | None, raw_text: str,
) -> dict:
    db = OwnerSessionLocal()
    try:
        # Placeholder classification values - overwritten below once the fingerprint
        # agent runs. Never left as "unclassified" silently: degraded_mode in the
        # response tells the caller whether that actually happened.
        matter = Matter(
            title=title, client_name=client_name, practice_area="unclassified",
            jurisdiction="unclassified", matter_type="unclassified", status="closed",
            opened_date=opened_date,
        )
        db.add(matter)
        db.flush()

        db.add(AccessGrant(matter_id=matter.id, user_id=user_id, grant_level="write", granted_by=user_id))
        db.flush()

        doc = await ingest_document(db, str(matter.id), doc_title, doc_type, confidentiality_tier, raw_text)
        db.flush()

        fingerprint_row, degraded = await build_matter_fingerprint(db, str(matter.id), raw_text)
        if fingerprint_row is not None:
            matter.practice_area = fingerprint_row.practice_area
            matter.jurisdiction = fingerprint_row.jurisdiction
            factual_pattern = fingerprint_row.factual_pattern or {}
            matter.matter_type = factual_pattern.get("matter_type") or matter.matter_type

        citations_linked: list[dict] = []
        if not degraded:
            citations_linked = await extract_and_link_citations(db, str(matter.id), doc)

        db.commit()
        return {
            "matter_id": str(matter.id),
            "document_id": str(doc.id),
            "degraded_mode": degraded,
            "jurisdiction": matter.jurisdiction,
            "practice_area": matter.practice_area,
            "matter_type": matter.matter_type,
            "citations_linked": citations_linked,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

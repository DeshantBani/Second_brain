"""Orchestrates the drafting workflow: session creation, the turn-by-turn intake
conversation, and final draft generation (template research + drafting agent). Unlike
the query pipeline this isn't a single request/response - it's genuinely stateful
across several HTTP calls, so state lives on the DraftingSession row itself rather than
in an in-memory graph."""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents_sdk.client import AgentError
from app.agents_sdk.drafting_agent import run_drafting_agent
from app.agents_sdk.drafting_intake_agent import run_drafting_intake_agent
from app.agents_sdk.schemas import GatheredRequirements, PetitionSection
from app.agents_sdk.template_research_agent import run_template_research_agent
from app.models.drafting_session import DraftingSession

logger = logging.getLogger("second_brain.drafting")

# Last-resort fallback if the template research agent itself is unreachable (not just
# "found nothing online" - that case is handled inside the agent) - a hardcoded,
# conventional Indian petition structure so drafting never fully blocks on a live call.
FALLBACK_STRUCTURE = [
    PetitionSection(name="Cause Title", description="Court/tribunal name, parties, and case number formatting"),
    PetitionSection(name="Memorandum of Parties", description="Full names, descriptions, and addresses of petitioner(s) and respondent(s)"),
    PetitionSection(name="Synopsis", description="Brief overview of the matter and the relief sought"),
    PetitionSection(name="List of Dates and Events", description="Chronological table of material dates"),
    PetitionSection(name="Statement of Facts", description="Numbered paragraphs setting out the operative facts"),
    PetitionSection(name="Grounds", description="Numbered paragraphs setting out the legal grounds relied upon"),
    PetitionSection(name="Prayer", description="The specific relief sought from the court/tribunal"),
    PetitionSection(name="Verification", description="Standard verification clause"),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _advance_intake(session: DraftingSession) -> None:
    try:
        result = await run_drafting_intake_agent(session.case_brief, session.conversation)
    except AgentError as exc:
        logger.warning("drafting intake agent unavailable: %s", exc)
        session.degraded_mode = True
        return

    if result.ready_to_draft and result.gathered_requirements:
        session.status = "ready"
        session.gathered_requirements = result.gathered_requirements.model_dump()
    else:
        session.status = "gathering"
        session.conversation = [*session.conversation, {"role": "assistant", "content": result.next_question, "at": _now_iso()}]


async def create_drafting_session(db: Session, user_id: str, case_brief: str) -> DraftingSession:
    session = DraftingSession(user_id=user_id, case_brief=case_brief, status="gathering", conversation=[])
    db.add(session)
    db.flush()
    await _advance_intake(session)
    db.flush()
    return session


async def add_message(db: Session, session: DraftingSession, message: str) -> DraftingSession:
    session.conversation = [*session.conversation, {"role": "user", "content": message, "at": _now_iso()}]
    await _advance_intake(session)
    db.flush()
    return session


async def generate_draft(db: Session, session: DraftingSession) -> DraftingSession:
    if session.gathered_requirements is None:
        raise ValueError("session is not ready to draft yet - requirements not gathered")

    requirements = GatheredRequirements(**session.gathered_requirements)

    try:
        template_result = await run_template_research_agent(requirements.petition_type)
        sections = template_result.sections or FALLBACK_STRUCTURE
        session.template_structure = template_result.model_dump()
    except AgentError as exc:
        logger.warning("template research unavailable, using fallback structure: %s", exc)
        sections = FALLBACK_STRUCTURE
        session.template_structure = {"sections": [s.model_dump() for s in sections], "grounded_in_sources": False, "notes": "Template research was unavailable - standard structure used."}
        session.degraded_mode = True

    try:
        draft_result = await run_drafting_agent(session.case_brief, requirements, sections)
        session.draft_sections = [s.model_dump() for s in draft_result.sections]
        session.status = "drafted"
    except AgentError as exc:
        logger.warning("drafting agent unavailable: %s", exc)
        session.degraded_mode = True

    db.flush()
    return session

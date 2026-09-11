import logging

from sqlalchemy.orm import Session

from app.agents_sdk.client import AgentError
from app.agents_sdk.proofreading_agent import run_proofreading_agent
from app.models.proofreading_report import ProofreadingReport

logger = logging.getLogger("second_brain.proofreading")


async def run_proofreading(db: Session, user_id: str, draft_text: str, case_brief: str | None) -> ProofreadingReport:
    report = ProofreadingReport(user_id=user_id, case_brief=case_brief, draft_text=draft_text, findings=[], summary="")
    try:
        result = await run_proofreading_agent(draft_text, case_brief)
        report.findings = [f.model_dump() for f in result.findings]
        report.summary = result.summary
    except AgentError as exc:
        logger.warning("proofreading agent unavailable: %s", exc)
        report.degraded_mode = True
        report.summary = "The reasoning engine was unavailable, so no automated review could be produced. Please proofread manually."

    db.add(report)
    db.flush()
    return report

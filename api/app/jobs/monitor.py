"""Background authority-monitoring job (build plan Section 7): independent of the query
path, periodically re-checks every Authority against the active CaseLawProvider and
flags any ReliabilityAssessment that depended on one whose status has moved. Never
imports a concrete provider - only the factory - so this job works unmodified
regardless of whether CASE_LAW_PROVIDER is mock or indiankanoon."""
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import OwnerSessionLocal
from app.jobs.celery_app import celery_app
from app.models.authority import Authority
from app.models.reliability import ReliabilityAssessment
from app.reliability.factory import get_case_law_provider

logger = logging.getLogger("second_brain.monitor")


@celery_app.task(name="app.jobs.monitor.recheck_all_authorities")
def recheck_all_authorities() -> dict:
    provider = get_case_law_provider()
    db = OwnerSessionLocal()
    changed = 0
    flagged = 0
    try:
        authorities = db.execute(select(Authority)).scalars().all()
        for authority in authorities:
            live = provider.get_citation_status(authority.citation)
            status_changed = live.status != authority.status

            authority.status = live.status
            authority.treatment_history = [e.model_dump(mode="json") for e in live.treatment_history]
            authority.last_checked_at = datetime.now(timezone.utc)
            authority.monitoring_status = "checked_flagged" if live.treatment_history else "checked_clear"

            if status_changed:
                changed += 1
                dependents = db.execute(
                    select(ReliabilityAssessment).where(ReliabilityAssessment.authority_id == authority.id)
                ).scalars().all()
                for dep in dependents:
                    dep.needs_review = True
                    dep.stale = True
                    flagged += 1

        db.commit()
        logger.info("authority recheck complete: %d changed, %d assessments flagged", changed, flagged)
        return {"checked": len(authorities), "changed": changed, "flagged": flagged}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

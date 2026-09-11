import pytest

from app.agents_sdk.citation_guardrail import check_reliability_output
from app.agents_sdk.schemas import FreshWorkPoint, ProviderSource, ReliabilityAssessmentSchema, SourceRef

CONTINENTAL = "Continental Constructions Co. Ltd v. State Trading Corporation of India, AIR 1997 Del 217"


def _make_assessment(status: str, excerpt: str, verdict: str = "amber", monitoring_status: str = "checked_flagged"):
    return ReliabilityAssessmentSchema(
        verdict=verdict,
        monitoring_status=monitoring_status,
        reasoning="Verify the cure-period holding against the negative treatment before relying on it further.",
        points_needing_fresh_work=[
            FreshWorkPoint(
                point="Re-examine the cure period argument",
                source_ref=SourceRef(document_id="doc-1", page=3, paragraph=12, quote="cure period"),
            )
        ],
        sources=[ProviderSource(citation=CONTINENTAL, status=status, treatment_excerpt=excerpt)],
    )


@pytest.mark.asyncio
async def test_grounded_excerpt_passes():
    assessment = _make_assessment(
        status="doubted",
        excerpt="prior to expiry of the cure period, already asserted a claim for damages",
    )
    result = await check_reliability_output(assessment)
    assert result.tripwire_triggered is False


@pytest.mark.asyncio
async def test_fabricated_excerpt_trips_the_guardrail():
    assessment = _make_assessment(
        status="doubted",
        excerpt="This citation completely fabricated wording that appears nowhere in the record",
    )
    result = await check_reliability_output(assessment)
    assert result.tripwire_triggered is True
    assert result.output_info["failures"]


@pytest.mark.asyncio
async def test_status_mismatch_trips_the_guardrail():
    assessment = _make_assessment(
        status="good_law",  # wrong - fixture says doubted
        excerpt="prior to expiry of the cure period, already asserted a claim for damages",
    )
    result = await check_reliability_output(assessment)
    assert result.tripwire_triggered is True


@pytest.mark.asyncio
async def test_green_with_flagged_monitoring_is_inconsistent():
    assessment = _make_assessment(
        status="doubted",
        excerpt="prior to expiry of the cure period, already asserted a claim for damages",
        verdict="green",
        monitoring_status="checked_flagged",
    )
    result = await check_reliability_output(assessment)
    assert result.tripwire_triggered is True

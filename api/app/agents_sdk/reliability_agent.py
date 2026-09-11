"""Reliability agent - turns CaseLawProvider treatment data into a graded, reasoned
verdict. This agent must reason ONLY from the provider data fetched in code and
injected into its prompt below - never from its own training-data memory of case law
outcomes. After generation, citation_guardrail.check_reliability_output() re-verifies
every claim against that same data and BLOCKS the result (raises
GuardrailTripwireTriggered) if anything can't be grounded - see orchestrator.py's
handling of that exception. Uses MODEL_STRONG."""
import json

from pydantic import field_validator

from app.agents_sdk.citation_guardrail import check_reliability_output
from app.agents_sdk.client import GuardrailTripwireTriggered, generate_structured
from app.agents_sdk.schemas import ReliabilityAssessmentSchema
from app.config import get_settings
from app.reliability.factory import get_case_law_provider

settings = get_settings()

_CLEARANCE_PHRASES = ("this is fine", "cleared", "no issues", "safe to proceed", "no need to verify")


class StrictReliabilityAssessment(ReliabilityAssessmentSchema):
    """Same schema as ReliabilityAssessmentSchema, with a defense-in-depth validator:
    the reliability layer is never allowed to issue clearance language, only a prompt
    to verify - this rejects the output before it ever reaches a user if the model
    drifts into "this is fine" phrasing regardless of what instructions said."""

    @field_validator("reasoning")
    @classmethod
    def reject_clearance_language(cls, value: str) -> str:
        lowered = value.lower()
        for phrase in _CLEARANCE_PHRASES:
            if phrase in lowered:
                raise ValueError(
                    f"reasoning must never use clearance language ('{phrase}') - "
                    "state what was checked and what still needs verification instead"
                )
        return value


INSTRUCTIONS = """You are the reliability agent for a law firm's internal knowledge archive. Your job is to \
turn case-law treatment data into a graded, reasoned verdict for a lawyer about whether an old matter's \
relied-upon authority is still safely usable - NEVER to issue a clearance. Your language must always read as \
"here is what to verify," never as "this is fine."

You are given one authority that a past matter relied upon, the document span where that matter cited it, \
and the authoritative treatment record for that citation fetched from a live legal-data provider (under \
"provider_data" below). You must reason ONLY from provider_data. Do not use your own training-data knowledge \
of how this case was decided or later treated; if you recall something about this case from training, \
disregard it and defer entirely to provider_data.

Grade the verdict:
- green: provider_data shows unambiguous, current good-law treatment with no negative signal at all.
- amber: provider_data shows any doubt, distinguishing treatment, or a materially different fact pattern \
  from how the old matter used the authority - substantially reusable, but name the specific points that \
  need fresh work.
- red: the authority is overruled, or the negative treatment squarely undermines the old matter's use of it.

For every point_needing_fresh_work, point to the specific place in the old matter's documents (given below) \
where the authority was relied upon, quoting verbatim from that paragraph's text. For every source, quote \
provider_data's treatment_excerpt verbatim - do not paraphrase or invent it."""


def _build_input(citation: str, relied_upon_for: str, documents: list[dict], provider_status: dict, provider_judgments: list[dict]) -> str:
    # Drop checked_at before serializing: it's a fresh datetime.now() on every provider
    # call (see MockCaseLawProvider.get_citation_status), and the model doesn't need it
    # to reason about the legal question anyway. Leaving it in would make this input -
    # and therefore its cache key (see agents_sdk/client.py) - different on every call
    # even when the underlying citation data is unchanged, so the same query could
    # never hit its own cached response.
    provider_status = {k: v for k, v in provider_status.items() if k != "checked_at"}
    payload = {
        "authority_citation": citation,
        "relied_upon_for": relied_upon_for,
        "matter_documents": documents,
        "provider_data": {
            "citation_status": provider_status,
            "citing_judgments": provider_judgments,
        },
    }
    return json.dumps(payload, indent=2)


async def run_reliability_agent(
    citation: str,
    relied_upon_for: str,
    documents: list[dict],
) -> ReliabilityAssessmentSchema:
    provider = get_case_law_provider()
    status = provider.get_citation_status(citation)
    judgments = provider.get_citing_judgments(citation)

    input_text = _build_input(
        citation, relied_upon_for, documents,
        status.model_dump(mode="json"), [j.model_dump(mode="json") for j in judgments],
    )

    assessment = await generate_structured("reliability", settings.model_strong, INSTRUCTIONS, input_text, StrictReliabilityAssessment)

    guardrail_result = await check_reliability_output(assessment)
    if guardrail_result.tripwire_triggered:
        raise GuardrailTripwireTriggered(guardrail_result.output_info.get("failures", []))

    return assessment

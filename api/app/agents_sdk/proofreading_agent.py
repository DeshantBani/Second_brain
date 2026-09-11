"""Proofreading agent - reviews a lawyer's already-drafted petition for format issues,
content issues, and (when a case brief is supplied) facts present in the case but
missing from the draft. Framed the same way as the reliability layer elsewhere in this
system: findings are always a prompt to verify, never a clearance - summary must never
read as "this is fine," only as what to check."""
import json

from pydantic import field_validator

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import ProofreadingResult
from app.config import get_settings

settings = get_settings()

_CLEARANCE_PHRASES = ("this is fine", "no issues", "ready to file", "safe to file", "looks good")


class StrictProofreadingResult(ProofreadingResult):
    @field_validator("summary")
    @classmethod
    def reject_clearance_language(cls, value: str) -> str:
        lowered = value.lower()
        for phrase in _CLEARANCE_PHRASES:
            if phrase in lowered:
                raise ValueError(f"summary must never use clearance language ('{phrase}') - describe what to verify instead")
        return value


INSTRUCTIONS = """You are a legal drafting proofreader. You are given a draft petition/application and, where \
supplied, the case brief it should be based on.

Review for three kinds of issues:
- format: structural problems - missing conventional sections (cause title, verification, etc.), wrong \
  ordering, inconsistent numbering, prayer not matching the grounds argued.
- content: substantive drafting issues - a ground asserted but not actually argued, an ambiguous or internally \
  inconsistent statement, a legal argument that doesn't hold together.
- missing_fact: ONLY when a case brief is supplied - a fact stated in the case brief that does not appear \
  anywhere in the draft, and which is material to the petition. For every missing_fact finding, quote the \
  exact excerpt from the case brief that supports it in grounding_excerpt - never claim a fact is missing \
  without being able to point to it in the brief you were given.

Do not invent issues to seem thorough - if a section is genuinely fine, do not raise a finding about it. Your \
summary must never say the draft is "fine," "ready," or has "no issues" - always frame it as what should be \
verified before filing, even when the draft is generally strong."""


def build_input(draft_text: str, case_brief: str | None) -> str:
    return json.dumps({"draft_text": draft_text, "case_brief": case_brief or ""}, indent=2)


async def run_proofreading_agent(draft_text: str, case_brief: str | None) -> ProofreadingResult:
    return await generate_structured(
        "proofreading", settings.model_strong, INSTRUCTIONS,
        build_input(draft_text, case_brief), StrictProofreadingResult,
    )

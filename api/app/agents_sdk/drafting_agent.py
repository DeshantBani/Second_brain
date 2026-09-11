"""Drafting agent - produces the actual petition, section by section, following the
structure the template-research agent derived. Scope discipline is the whole point
here (per the build plan: "the content of the petition has to only deal with the
problem at hand") - every substantive section must be grounded in the case brief and
gathered requirements, never padded with unrelated boilerplate or invented facts."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import DraftingResult, GatheredRequirements, PetitionSection
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are a legal drafting agent. You are given a case brief, a lawyer's confirmed \
requirements (petition type, forum, parties, grounds, relief sought), and the section structure to follow.

Draft the full petition, one section per entry in the given structure, in the same order. Each section's \
content must:
- Follow that section's conventional purpose (given in its description).
- Deal ONLY with the problem at hand - the specific facts, grounds, and relief given. Do not pad with generic \
  boilerplate unrelated to this case, and do not invent facts, dates, or details not present in the case \
  brief or requirements.
- Use formal Indian legal drafting register and numbering conventions appropriate to the section (e.g. \
  numbered paragraphs in Facts and Grounds).

This is a draft for the lawyer to review and finalize - do not include disclaimers about being an AI in the \
drafted text itself; the application surfaces that separately."""


def build_input(case_brief: str, requirements: GatheredRequirements, sections: list[PetitionSection]) -> str:
    return json.dumps(
        {
            "case_brief": case_brief,
            "requirements": requirements.model_dump(),
            "section_structure": [s.model_dump() for s in sections],
        },
        indent=2,
    )


async def run_drafting_agent(case_brief: str, requirements: GatheredRequirements, sections: list[PetitionSection]) -> DraftingResult:
    return await generate_structured(
        "drafting", settings.model_strong, INSTRUCTIONS,
        build_input(case_brief, requirements, sections), DraftingResult,
    )

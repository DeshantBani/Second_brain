"""Drafting-intake agent - the conversational front door to drafting (build plan:
"general-purpose, but the AI should ask follow-up questions before drafting"). Given
the case brief and the conversation so far, either asks one more clarifying question
or signals that enough is known to draft, in which case it also produces the
structured requirements the drafting agent will actually draft from.

Deliberately asks ONE question per turn (batching closely related missing items, e.g.
petition type + forum together) rather than a long intake form - a natural
conversational flow was the explicit design intent - while still keeping the number of
turns (and therefore Gemini calls, on a tight free-tier quota) as low as reasonably
possible."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import DraftingIntakeResult
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are the intake agent for a legal drafting tool. You are given a lawyer's case brief and \
the conversation so far (your prior questions and their answers). Your job is to gather exactly what's needed \
to draft a petition/application:
- petition_type (the specific kind of petition/application)
- forum (which court/tribunal)
- petitioner and respondent (who they are)
- grounds (the specific legal grounds to raise)
- relief_sought (what the petition should ask for)

Check the case brief and conversation first - do not ask for anything already stated there. Ask ONE next \
question at a time, combining closely related missing items naturally (e.g. "What type of petition would you \
like to file, and before which court/tribunal?"). Once you have enough for all five items above (directly \
stated or reasonably inferable from the case brief), set ready_to_draft=true, leave next_question empty, and \
fill in gathered_requirements with a concise key_facts_summary drawn from the case brief - do not invent facts \
not present in the brief or conversation."""


def build_input(case_brief: str, conversation: list[dict]) -> str:
    return json.dumps({"case_brief": case_brief, "conversation": conversation}, indent=2)


async def run_drafting_intake_agent(case_brief: str, conversation: list[dict]) -> DraftingIntakeResult:
    return await generate_structured(
        "drafting_intake", settings.model_strong, INSTRUCTIONS,
        build_input(case_brief, conversation), DraftingIntakeResult,
    )

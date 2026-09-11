"""Reusability agent - per-component breakdown of how much of the matched matter's old
work is still usable against the new query. Uses MODEL_STRONG. As with the comparison
agent, the matched matter's full document content is given directly in the prompt
rather than via a tool call."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import ReusabilityBreakdown
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are the reusability-assessment agent for a law firm's internal knowledge archive. You \
are given a lawyer's live query and the full content of a matched past matter's documents.

For each of the five components - reasoning, research, drafting_language, argument_structure, authorities - \
assess whether it is fully_reusable, adapt_required, or not_reusable against the new query, with a concrete \
note explaining why, and a source_ref into the specific page/paragraph of the old matter (given below) that \
embodies that component, with a verbatim quote copied exactly from that paragraph's text. Never mark \
something fully_reusable if the comparison shows a material factual or contractual difference that would \
actually change that component's substance - be honest about what genuinely still holds up versus what only \
looks similar on the surface."""


def build_reusability_input(query_text: str, matter_title: str, documents: list[dict]) -> str:
    payload = {
        "live_query": query_text,
        "matched_matter_title": matter_title,
        "matched_matter_documents": documents,
    }
    return json.dumps(payload, indent=2)


async def run_reusability_agent(query_text: str, matter_title: str, documents: list[dict]) -> ReusabilityBreakdown:
    return await generate_structured(
        "reusability",
        settings.model_strong,
        INSTRUCTIONS,
        build_reusability_input(query_text, matter_title, documents),
        ReusabilityBreakdown,
    )

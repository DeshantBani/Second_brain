"""Template research agent - turns whatever real web pages
services/web_research.py managed to fetch into a structured petition format (ordered
sections + what each contains). This is an LLM synthesis step over real fetched text,
not a search itself - the search/fetch is plain code specifically so it can fail
honestly (empty list) rather than an agent inventing having browsed something.

If no usable source was fetched, this still runs - the instructions require it to say
so plainly (grounded_in_sources=false) and fall back to the well-established
conventional structure for the petition type, rather than blocking drafting entirely
on a flaky third-party search endpoint."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import TemplateStructureResult
from app.config import get_settings
from app.services.web_research import research_sources

settings = get_settings()

INSTRUCTIONS = """You are a legal-drafting-format research agent. You are given a petition type and, where \
available, excerpts from real web pages that were actually fetched while researching that petition type's \
conventional format in India.

If usable source excerpts are provided, derive the ordered section structure (e.g. Cause Title, Memorandum \
of Parties, Synopsis, List of Dates and Events, Statement of Facts, Grounds, Prayer, Verification, Affidavit) \
from what those sources actually show, and set grounded_in_sources=true. Cite which source most informed the \
structure in your notes.

If no source excerpts are provided, or none of them are actually usable (e.g. they're login walls, error \
pages, or unrelated content), do NOT pretend to have found something - fall back to the well-established \
conventional structure for this petition type under Indian civil/commercial procedure, set \
grounded_in_sources=false, and say so plainly in notes.

Never fabricate having seen a source that wasn't given to you."""


def build_input(petition_type: str, sources: list[dict]) -> str:
    return json.dumps({"petition_type": petition_type, "fetched_sources": sources}, indent=2)


async def run_template_research_agent(petition_type: str) -> TemplateStructureResult:
    sources = research_sources(f"{petition_type} format India sample petition draft")
    return await generate_structured(
        "template_research", settings.model_strong, INSTRUCTIONS,
        build_input(petition_type, sources), TemplateStructureResult,
    )

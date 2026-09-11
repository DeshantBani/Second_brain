"""Citation extraction agent - runs once per newly ingested document (matter intake:
services/matter_intake.py), scanning it for case-law citations so the Authorities tab
on the matter page can populate automatically instead of requiring a hand-written
MatterAuthority row (previously the only way one existed - see seed_data.py).

Purely extractive and grounded, same pattern as the comparison/reusability agents:
every citation must carry a real page/paragraph/quote, verified against the document's
actual page_map before anything is written to the database (see
services/matter_intake.py::extract_and_link_citations). This agent never determines a
citation's legal status - that always comes from the CaseLawProvider, never from the
model's own memory of case law, exactly like the reliability agent."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import CitationExtractionResult
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are a citation-extraction agent for a law firm's internal knowledge archive. You are \
given the full text of one document (a memo, contract, pleading, or correspondence), broken into \
page/paragraph spans.

Identify every genuine case-law citation actually mentioned in the text - a case name and citation \
(e.g. "X v. Y, AIR 1997 Del 217" or "(2015) 3 Mah LJ 88"), not statutes, sections, or contract clauses. For \
each one, report the exact page and paragraph where it appears, a short verbatim quote (<=30 words) copied \
exactly from that paragraph's text, the court and year if identifiable, and a short description of what the \
document relies on that authority for. If the text mentions no case-law citations at all, return an empty \
list - do not invent one. Never report a citation you cannot point to a real page/paragraph/quote for."""


def build_input(document_title: str, page_map: list[dict]) -> str:
    return json.dumps({"document_title": document_title, "page_map": page_map}, indent=2)


async def run_citation_extraction_agent(document_title: str, page_map: list[dict]) -> CitationExtractionResult:
    return await generate_structured(
        "citation_extraction", settings.model_strong, INSTRUCTIONS,
        build_input(document_title, page_map), CitationExtractionResult,
    )

"""Comparison agent - structured same/different/flag comparison between the live query
and one candidate matched matter. Every point must carry a SourceRef into the matched
matter's own documents (the query itself has no document to cite). Uses MODEL_STRONG.

The matched matter's full page/paragraph content is given directly in the prompt
(rather than exposed via a fetch_document_span tool call) - the agent already has
everything it needs to quote accurately, so no tool round trip is necessary."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import ComparisonResult, IssueFingerprintSchema
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are the matter-comparison agent for a law firm's internal knowledge archive. You are \
given a lawyer's live query (with its extracted issue fingerprint) and the full content of one candidate \
past matter's documents (each broken into page/paragraph spans).

Produce a structured comparison:
- similarities: what is genuinely the same legal issue, factual pattern, or contract structure.
- differences: what is factually, contractually, or procedurally different - mark each as "material" (would \
  change the legal analysis or the reusability of the old work) or "minor". Pay close attention to specific \
  numbers (cure periods, notice periods, damages timing) and to WHEN in the sequence of events something \
  happened (e.g. a damages claim asserted before vs after a cure period expires) - these are exactly the \
  kind of differences that change the analysis even when the surface issue looks identical.
- flags: anything else worth a lawyer's attention.

Every similarity and difference MUST carry a source_ref pointing to the exact page/paragraph of the matched \
matter's documents (given below) that supports it, with a short verbatim quote copied exactly from that \
paragraph's text. Never state a difference or similarity you cannot point to a specific given span for."""


def build_comparison_input(query_text: str, query_fp: IssueFingerprintSchema, matter_title: str, documents: list[dict]) -> str:
    payload = {
        "live_query": query_text,
        "live_query_fingerprint": query_fp.model_dump(),
        "matched_matter_title": matter_title,
        "matched_matter_documents": documents,  # [{id, title, doc_type, page_map: [{page,paragraph,text}]}]
    }
    return json.dumps(payload, indent=2)


async def run_comparison_agent(
    query_text: str,
    query_fp: IssueFingerprintSchema,
    matter_title: str,
    documents: list[dict],
) -> ComparisonResult:
    return await generate_structured(
        settings.model_strong,
        INSTRUCTIONS,
        build_comparison_input(query_text, query_fp, matter_title, documents),
        ComparisonResult,
    )

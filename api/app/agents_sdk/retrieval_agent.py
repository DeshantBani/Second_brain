"""Retrieval agent - the third stage of the funnel (see services/orchestrator.py for
stages 1-2). Reasons over the full fingerprint of each already-filtered, already
vector-ranked candidate, not just embedding distance, and must be willing to say
"no confident match" rather than force-rank weak candidates. Uses MODEL_FAST."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import IssueFingerprintSchema, RetrievalResult
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = """You are the retrieval-ranking agent for a law firm's internal matter archive. You will be \
given the issue fingerprint of an incoming query and a shortlist of candidate past matters (already \
filtered by metadata and embedding similarity) with their own fingerprints.

Rank the candidates by genuine legal-issue similarity - the same legal issue, a comparable factual pattern, \
comparable contract structure, and comparable procedural posture - not by surface keyword overlap. State a \
concrete rationale for each ranked result referencing specific fingerprint fields. \
If none of the candidates are a strong match, set no_confident_match=true and explain why rather than \
force-ranking weak candidates - a false positive here is worse than saying "no match"."""


def build_retrieval_input(query_fp: IssueFingerprintSchema, candidates: list[dict]) -> str:
    payload = {
        "query_fingerprint": query_fp.model_dump(),
        "candidates": candidates,  # [{matter_id, title, fingerprint}]
    }
    return json.dumps(payload, indent=2)


async def run_retrieval_agent(query_fp: IssueFingerprintSchema, candidates: list[dict]) -> RetrievalResult:
    return await generate_structured(
        "retrieval", settings.model_fast, INSTRUCTIONS, build_retrieval_input(query_fp, candidates), RetrievalResult
    )

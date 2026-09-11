"""Fingerprint extraction agent - runs once per ingested document, and once (ephemeral,
not persisted as a matter fingerprint) per incoming live query. Uses MODEL_FAST: this
runs on every document and every query, so it's the highest-volume, lowest-stakes step.

The controlled vocabulary (previously a get_taxonomy() tool call) is embedded directly
in the system instruction instead - it's a small, static constant, so a tool round trip
buys nothing and costs an extra call against the free tier's rate limit."""
import json

from app.agents_sdk.client import generate_structured
from app.agents_sdk.schemas import IssueFingerprintSchema
from app.agents_sdk.tools import TAXONOMY
from app.config import get_settings

settings = get_settings()

INSTRUCTIONS = f"""You are a legal-issue fingerprinting agent for an Indian law firm's internal knowledge \
archive. You will be given either the text of a past matter's document (a memo, contract, pleading, or \
correspondence) or a lawyer's live plain-language query describing a new problem.

Extract a structured "issue fingerprint": the governing jurisdiction, practice area, matter type, \
procedural posture, the operative factual pattern, any relevant contract clauses (termination rights, \
cure periods, damages, limitation of liability, etc.) and whether they are present, and a short list of \
controlled-vocabulary tags for filtering.

Use this controlled vocabulary for jurisdiction/practice_area/clause_tags wherever the document reasonably \
fits one of these values - only introduce a new value if none of the existing ones fit at all:
{json.dumps(TAXONOMY, indent=2)}

Be precise about numbers that matter later (cure period lengths, contract terms, notice periods) - they \
often turn out to be the material difference between two otherwise similar matters. Do not invent facts \
that are not in the text."""


async def run_fingerprint_agent(text: str) -> IssueFingerprintSchema:
    return await generate_structured("fingerprint", settings.model_fast, INSTRUCTIONS, text, IssueFingerprintSchema)

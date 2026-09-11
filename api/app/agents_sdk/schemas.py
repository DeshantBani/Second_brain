"""Structured-output schemas shared by every agent in the pipeline. Every substantive
claim an agent makes is required to carry a SourceRef - this is the mechanical backbone
of the "never assert without a source" constraint, and it's what the citation
verification guardrail (citation_guardrail.py) checks against.

These are plain Pydantic models (not ORM models) - client.generate_structured() passes
them to Gemini as `response_schema`, which returns a parsed instance directly.
"""
from typing import Literal

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """A pointer to the exact place in a document a claim comes from."""
    document_id: str = Field(description="UUID of the source document")
    page: int = Field(description="1-indexed page number")
    paragraph: int = Field(description="1-indexed paragraph number within the page")
    quote: str = Field(description="Short verbatim quote (<= 40 words) supporting the claim, copied exactly from the source")


# ---------------------------------------------------------------------------
# 1. Fingerprint extraction agent
# ---------------------------------------------------------------------------

class ContractClause(BaseModel):
    clause_type: str = Field(description="e.g. termination_for_convenience, termination_for_cause, limitation_of_liability")
    exists: bool
    key_terms: str = Field(description="Short free-text summary of the clause's operative terms, e.g. '30-day cure period'")


class IssueFingerprintSchema(BaseModel):
    jurisdiction: str = Field(description="Governing jurisdiction, e.g. 'India - Maharashtra' or 'India'")
    practice_area: str = Field(description="e.g. commercial_contracts, employment, arbitration, real_estate")
    matter_type: str = Field(description="Short label for the kind of matter, e.g. 'supply agreement termination'")
    procedural_posture: str = Field(description="Where the matter stands procedurally, e.g. 'pre-litigation advisory', 'active arbitration'")
    factual_pattern: str = Field(description="Dense prose summary of the operative facts")
    contract_clauses: list[ContractClause] = Field(description="Relevant clauses identified, with existence flags")
    clause_tags: list[str] = Field(description="Short controlled-vocabulary tags for SQL filtering, e.g. ['termination_for_convenience','cure_period','supply_agreement']")
    summary: str = Field(description="One or two sentence summary of the legal issue")


# ---------------------------------------------------------------------------
# 2. Retrieval agent
# ---------------------------------------------------------------------------

class RankedCandidate(BaseModel):
    matter_id: str
    rank: int
    similarity_rationale: str = Field(description="Why this matter is/isn't a strong match, referencing specific fingerprint fields")
    confidence: Literal["high", "medium", "low"]


class RetrievalResult(BaseModel):
    no_confident_match: bool = Field(description="True if the archive genuinely contains nothing close - do not force-rank weak candidates")
    rationale: str = Field(description="Explanation of the ranking decision, or of why no confident match exists")
    results: list[RankedCandidate]


# ---------------------------------------------------------------------------
# 3. Comparison agent
# ---------------------------------------------------------------------------

class ComparisonPoint(BaseModel):
    point: str
    source_ref: SourceRef


class DifferencePoint(BaseModel):
    point: str
    materiality: Literal["material", "minor"]
    source_ref: SourceRef


class ComparisonResult(BaseModel):
    summary: str
    similarities: list[ComparisonPoint]
    differences: list[DifferencePoint]
    flags: list[str] = Field(description="Anything else worth the lawyer's attention that isn't a clean similarity/difference")


# ---------------------------------------------------------------------------
# 4. Reusability agent
# ---------------------------------------------------------------------------

class ReusabilityComponent(BaseModel):
    component: Literal["reasoning", "research", "drafting_language", "argument_structure", "authorities"]
    reusability: Literal["fully_reusable", "adapt_required", "not_reusable"]
    notes: str
    source_ref: SourceRef


class ReusabilityBreakdown(BaseModel):
    components: list[ReusabilityComponent]


# ---------------------------------------------------------------------------
# 5. Reliability agent
# ---------------------------------------------------------------------------

class FreshWorkPoint(BaseModel):
    point: str = Field(description="A specific, named point of the old matter's reasoning that needs fresh work")
    source_ref: SourceRef


class ProviderSource(BaseModel):
    citation: str
    status: Literal["good_law", "doubted", "distinguished", "overruled"]
    treatment_excerpt: str = Field(description="Verbatim excerpt from the CaseLawProvider treatment record - never from the model's own memory")


class ReliabilityAssessmentSchema(BaseModel):
    verdict: Literal["green", "amber", "red"] = Field(
        description="A verdict is a prompt to verify, never a clearance. Amber/red whenever there is genuine "
        "doubt; green only when the provider data shows unambiguous, current good-law treatment."
    )
    monitoring_status: Literal["checked_clear", "checked_flagged"] = Field(
        description="Whether the provider-sourced check came back clear or flagged - distinct from 'not checked'"
    )
    reasoning: str = Field(description="Reasoning grounded ONLY in the supplied provider data, never in the model's own recollection of case law")
    points_needing_fresh_work: list[FreshWorkPoint]
    sources: list[ProviderSource]


# ---------------------------------------------------------------------------
# Assembled per-query result (not itself an agent output - built by the orchestrator)
# ---------------------------------------------------------------------------

class ReliabilityOutcome(BaseModel):
    """Wraps a ReliabilityAssessmentSchema OR records that the citation-verification
    guardrail withheld it. `verdict` is intentionally absent (never a fabricated
    fallback verdict) when blocked."""
    authority_citation: str
    blocked_by_guardrail: bool
    guardrail_failure_reasons: list[str] = Field(default_factory=list)
    assessment: ReliabilityAssessmentSchema | None = None

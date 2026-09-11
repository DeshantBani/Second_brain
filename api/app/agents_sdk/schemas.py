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
# 7. Citation extraction agent (matter intake - services/matter_intake.py)
# ---------------------------------------------------------------------------

class ExtractedCitation(BaseModel):
    """Purely extractive - the model may only report a citation it can point to an
    exact page/paragraph and quote for. It never determines the citation's legal
    status; services/matter_intake.py resolves that via the CaseLawProvider, exactly
    as the reliability agent does - this agent's job ends at 'this document mentions
    this case, here, for this reason.'"""
    citation: str = Field(description="The case citation exactly as written in the text, e.g. 'Continental Constructions Co. Ltd v. State Trading Corporation of India, AIR 1997 Del 217'")
    court: str = Field(description="Court name if stated in or near the citation, else 'Unknown'")
    year: int = Field(description="Year of the decision if determinable from the citation or surrounding text, else 0")
    relied_upon_for: str = Field(description="Short description of what the document relies on this authority for")
    page: int = Field(description="1-indexed page where this citation appears")
    paragraph: int = Field(description="1-indexed paragraph where this citation appears")
    quote: str = Field(description="Short verbatim quote (<=30 words) from that exact paragraph, copied exactly")


class CitationExtractionResult(BaseModel):
    citations: list[ExtractedCitation] = Field(description="Every case-law citation actually mentioned in the text - an empty list if none are")


# ---------------------------------------------------------------------------
# 8. Drafting-intake agent (agents_sdk/drafting_intake_agent.py)
# ---------------------------------------------------------------------------

class GatheredRequirements(BaseModel):
    petition_type: str = Field(description="The specific type of petition/application to draft, e.g. 'Petition under Section 34 of the Arbitration and Conciliation Act, 1996'")
    forum: str = Field(description="The court/tribunal the petition will be filed before")
    petitioner: str = Field(description="Name/description of the petitioner(s)")
    respondent: str = Field(description="Name/description of the respondent(s)")
    grounds: list[str] = Field(description="The specific legal grounds to be raised, as the lawyer specified or confirmed")
    relief_sought: str = Field(description="The relief/prayer the petition should seek")
    key_facts_summary: str = Field(description="A concise summary of the operative facts drawn from the case brief and conversation, to ground the draft")


class DraftingIntakeResult(BaseModel):
    ready_to_draft: bool = Field(description="True only once petition_type, forum, parties, grounds, and relief sought are all known - either from the case brief or the conversation")
    next_question: str = Field(description="The single next clarifying question to ask, combining related missing items where natural (e.g. petition type + forum together). Empty string if ready_to_draft is true")
    gathered_requirements: GatheredRequirements | None = Field(description="Filled in only when ready_to_draft is true - null otherwise")


# ---------------------------------------------------------------------------
# 9. Template research agent (agents_sdk/template_research_agent.py) - synthesizes
# fetched web pages (services/web_research.py does the actual searching/fetching)
# into a structured format; never invents having seen a source it wasn't given.
# ---------------------------------------------------------------------------

class PetitionSection(BaseModel):
    name: str = Field(description="Section name, e.g. 'Cause Title', 'Synopsis', 'Facts', 'Grounds', 'Prayer', 'Verification'")
    description: str = Field(description="What this section conventionally contains and how it should be drafted")


class TemplateStructureResult(BaseModel):
    sections: list[PetitionSection] = Field(description="The ordered section structure for this petition type, grounded in the source material given")
    grounded_in_sources: bool = Field(description="True only if this structure was actually derived from the provided source excerpts, false if none were usable and this is a standard/conventional structure instead")
    notes: str = Field(description="Any caveats - e.g. which source(s) most informed this, or that no usable source was found and this is the standard convention")


# ---------------------------------------------------------------------------
# 10. Drafting agent (agents_sdk/drafting_agent.py)
# ---------------------------------------------------------------------------

class DraftedSection(BaseModel):
    section_name: str
    content: str = Field(description="The drafted text for this section - grounded only in the case brief and gathered requirements, never inventing facts")


class DraftingResult(BaseModel):
    sections: list[DraftedSection] = Field(description="The full petition, in the order given by the template structure")


# ---------------------------------------------------------------------------
# 11. Proofreading agent (agents_sdk/proofreading_agent.py)
# ---------------------------------------------------------------------------

class ProofreadingFinding(BaseModel):
    category: Literal["format", "content", "missing_fact"] = Field(description="format = structural/section issues; content = substantive drafting issues; missing_fact = a fact present in the case brief but absent from the draft")
    severity: Literal["high", "medium", "low"]
    section: str = Field(description="The section of the draft this finding relates to, or 'general' if not section-specific")
    issue: str = Field(description="What is wrong")
    suggestion: str = Field(description="A concrete, specific fix")
    grounding_excerpt: str = Field(description="For 'missing_fact' findings, the exact excerpt from the case brief that supports this - empty string for other categories")


class ProofreadingResult(BaseModel):
    summary: str = Field(description="A short overall assessment - never phrased as clearance/approval, only as what to verify, matching this system's reliability layer convention")
    findings: list[ProofreadingFinding]


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

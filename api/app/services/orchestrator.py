"""The query pipeline, as an explicit LangGraph StateGraph: one fixed, code-driven
sequence (never an agent-decided step order - see build plan Section 4) that ties every
specialist agent together. Every edge below is declared in code, not decided by an
LLM - LangGraph just gives that fixed sequence an explicit, inspectable shape (and a
shared PipelineState) instead of a hand-built result dict threaded through nested
if/else branches.

Deliberately NOT using LangGraph's prebuilt agent/tool-calling abstractions
(create_react_agent, etc.) or LangChain's model wrappers - every node below still
calls the same directly-tested Gemini integration in agents_sdk/client.py (with its
retry-on-429/503 logic), which matters a great deal on a free-tier key's tight quota.
LangGraph here is purely an orchestration/state layer, not a new call path to the LLM.

The RLS-scoped `db` session passed into run_query_pipeline() means every SQL query the
graph's nodes run is already confined to matters the requesting user can see - so no
candidate outside that boundary is ever handed to an LLM in the first place, regardless
of fingerprint similarity."""
import logging

from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents_sdk.client import AgentError, GuardrailTripwireTriggered, trace
from app.agents_sdk.comparison_agent import run_comparison_agent
from app.agents_sdk.fingerprint_agent import run_fingerprint_agent
from app.agents_sdk.reliability_agent import run_reliability_agent
from app.agents_sdk.retrieval_agent import run_retrieval_agent
from app.agents_sdk.reusability_agent import run_reusability_agent
from app.models.authority import Authority
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.models.matter import Matter
from app.models.matter_authority import MatterAuthority
from app.models.reliability import ReliabilityAssessment
from app.services.audit import log_query
from app.services.embeddings import embed_text
from app.services.fingerprint_text import fingerprint_to_embedding_text
from app.services.pipeline_state import PipelineState

logger = logging.getLogger("second_brain.orchestrator")

MAX_STRUCTURED_CANDIDATES = 50
MAX_VECTOR_CANDIDATES = 15


# ---------------------------------------------------------------------------
# Plain helpers - pure DB/business logic, no framework dependency either way.
# Unchanged by the LangGraph refactor; called from inside node closures below.
# ---------------------------------------------------------------------------

def _structured_filter(db: Session, jurisdiction: str, practice_area: str, clause_tags: list[str]) -> list[str]:
    """Stage 1: cheap SQL/metadata filter. RLS already limits this to matters the
    current user can see - this just narrows "everything visible" to "plausible"."""
    query = select(IssueFingerprint.matter_id).where(IssueFingerprint.matter_id.isnot(None))

    jurisdiction_root = jurisdiction.split(" - ")[0].strip() if jurisdiction else ""
    conditions = []
    if practice_area:
        conditions.append(IssueFingerprint.practice_area == practice_area)
    if clause_tags:
        conditions.append(IssueFingerprint.clause_tags.overlap(clause_tags))
    if jurisdiction_root:
        conditions.append(IssueFingerprint.jurisdiction.ilike(f"%{jurisdiction_root}%"))

    if conditions:
        from sqlalchemy import or_
        query = query.where(or_(*conditions))

    query = query.limit(MAX_STRUCTURED_CANDIDATES)
    rows = db.execute(query).scalars().all()
    return [str(r) for r in rows]


def _vector_rank(db: Session, candidate_matter_ids: list[str], query_vector: list[float] | None) -> list[dict]:
    """Stage 2: dense retrieval over the structurally filtered set. Falls back to
    filter order (no ranking signal) if embeddings are unavailable (degraded mode)."""
    if not candidate_matter_ids:
        return []

    base_query = (
        select(Matter, IssueFingerprint)
        .join(IssueFingerprint, IssueFingerprint.matter_id == Matter.id)
        .where(Matter.id.in_(candidate_matter_ids))
    )
    if query_vector is not None:
        base_query = base_query.order_by(IssueFingerprint.embedding.cosine_distance(query_vector))
    rows = db.execute(base_query.limit(MAX_VECTOR_CANDIDATES)).all()

    return [
        {
            "matter_id": str(matter.id),
            "title": matter.title,
            "client_name": matter.client_name,
            "practice_area": matter.practice_area,
            "jurisdiction": matter.jurisdiction,
            "fingerprint": {
                "jurisdiction": fp.jurisdiction,
                "practice_area": fp.practice_area,
                "procedural_posture": fp.procedural_posture,
                "factual_pattern": fp.factual_pattern,
                "contract_clauses": fp.contract_clauses,
                "clause_tags": fp.clause_tags,
                "summary": fp.summary,
            },
        }
        for matter, fp in rows
    ]


def _document_payload(db: Session, matter_id: str) -> list[dict]:
    docs = db.execute(select(Document).where(Document.matter_id == matter_id)).scalars().all()
    return [
        {"id": str(d.id), "title": d.title, "doc_type": d.doc_type, "page_map": d.page_map}
        for d in docs
    ]


def _matter_authorities(db: Session, matter_id: str) -> list[dict]:
    rows = db.execute(
        select(MatterAuthority, Authority)
        .join(Authority, Authority.id == MatterAuthority.authority_id)
        .where(MatterAuthority.matter_id == matter_id)
    ).all()
    return [
        {
            "matter_authority_id": str(ma.id),
            "authority_id": str(auth.id),
            "citation": auth.citation,
            "court": auth.court,
            "year": auth.year,
            "relied_upon_for": ma.relied_upon_for,
            "cited_in_document_id": str(ma.cited_in_document_id),
            "cited_at_page": ma.cited_at_page,
            "cited_at_paragraph": ma.cited_at_paragraph,
        }
        for ma, auth in rows
    ]


def _no_match_result(query_text: str, rationale: str, degraded_mode: bool, query_fp: dict | None) -> dict:
    return {
        "no_confident_match": True,
        "rationale": rationale,
        "degraded_mode": degraded_mode,
        "query_fingerprint": query_fp,
        "ranked_matters": [],
        "top_matter": None,
        "comparison": None,
        "reusability": None,
        "reliability": [],
    }


# ---------------------------------------------------------------------------
# Graph construction. Nodes are closures over `db` (an RLS-scoped, per-request
# session) - built fresh per request in run_query_pipeline(), which is cheap
# (StateGraph.compile() does no I/O) and keeps every node's DB access properly
# scoped to the requesting user without needing a context/config-passing scheme.
# ---------------------------------------------------------------------------

def _build_graph(db: Session):
    def finalize(state: PipelineState, result: dict, *, candidate_ids: list[str], results_returned: list,
                 sources_cited: list, no_confident_match: bool, degraded_mode: bool) -> dict:
        result["query_text"] = state["query_text"]
        log = log_query(
            db, state["user_id"], state["source"], state["query_text"], state.get("query_fp_dict"),
            matter_access_scope=candidate_ids, results_returned=results_returned, sources_cited=sources_cited,
            no_confident_match=no_confident_match, degraded_mode=degraded_mode, full_result=result,
        )
        result["query_log_id"] = str(log.id)
        return {"result": result}

    async def fingerprint_node(state: PipelineState) -> dict:
        try:
            query_fp = await run_fingerprint_agent(state["query_text"])
            return {"query_fp": query_fp, "query_fp_dict": query_fp.model_dump()}
        except AgentError as exc:
            logger.warning("fingerprint agent unavailable, degrading: %s", exc)
            return {"query_fp": None, "query_fp_dict": None, "degraded_mode": True}

    def route_after_fingerprint(state: PipelineState) -> str:
        return "no_fingerprint" if state.get("query_fp") is None else "continue"

    async def finalize_no_fingerprint_node(state: PipelineState) -> dict:
        result = _no_match_result(
            state["query_text"],
            "The reasoning engine is currently unavailable (Gemini not configured or unreachable), "
            "so no ranked comparison could be produced.",
            True, None,
        )
        return finalize(state, result, candidate_ids=[], results_returned=[], sources_cited=[],
                         no_confident_match=True, degraded_mode=True)

    async def retrieve_candidates_node(state: PipelineState) -> dict:
        query_fp = state["query_fp"]
        candidate_ids = _structured_filter(db, query_fp.jurisdiction, query_fp.practice_area, query_fp.clause_tags)
        if not candidate_ids:
            return {"candidate_ids": []}

        query_vector = embed_text(fingerprint_to_embedding_text(query_fp))
        update: dict = {
            "candidate_ids": candidate_ids,
            "candidates": _vector_rank(db, candidate_ids, query_vector),
        }
        if query_vector is None:
            update["degraded_mode"] = True
        return update

    def route_after_candidates(state: PipelineState) -> str:
        return "no_candidates" if not state.get("candidate_ids") else "continue"

    async def finalize_no_candidates_node(state: PipelineState) -> dict:
        result = _no_match_result(
            state["query_text"],
            "No matters in the archive share this issue's jurisdiction, practice area, or clause profile.",
            state.get("degraded_mode", False), state.get("query_fp_dict"),
        )
        return finalize(state, result, candidate_ids=[], results_returned=[], sources_cited=[],
                         no_confident_match=True, degraded_mode=state.get("degraded_mode", False))

    async def retrieval_rank_node(state: PipelineState) -> dict:
        try:
            ranked = await run_retrieval_agent(state["query_fp"], state["candidates"])
            return {"ranked": ranked, "retrieval_failed": False}
        except AgentError as exc:
            logger.warning("retrieval agent unavailable, degrading: %s", exc)
            return {"ranked": None, "retrieval_failed": True, "degraded_mode": True}

    def route_after_retrieval(state: PipelineState) -> str:
        if state.get("retrieval_failed"):
            return "retrieval_failed"
        ranked = state["ranked"]
        if ranked.no_confident_match or not ranked.results:
            return "no_confident_match"
        return "continue"

    async def finalize_retrieval_failed_node(state: PipelineState) -> dict:
        candidates = state.get("candidates", [])
        ranked_matters = [
            {
                "matter_id": c["matter_id"], "title": c["title"], "client_name": c["client_name"],
                "practice_area": c["practice_area"], "jurisdiction": c["jurisdiction"],
                "rank": i + 1, "similarity_rationale": "Ranked by structural/vector filtering only (degraded mode).",
                "confidence": "low",
            }
            for i, c in enumerate(candidates)
        ]
        result = _no_match_result(
            state["query_text"],
            "The reasoning engine could not rank candidates right now; here is the raw shortlist by "
            "structured/vector filtering only.",
            True, state.get("query_fp_dict"),
        )
        result["ranked_matters"] = ranked_matters
        return finalize(state, result, candidate_ids=state.get("candidate_ids", []), results_returned=ranked_matters,
                         sources_cited=[], no_confident_match=True, degraded_mode=True)

    async def finalize_no_confident_match_node(state: PipelineState) -> dict:
        ranked = state["ranked"]
        result = _no_match_result(state["query_text"], ranked.rationale, state.get("degraded_mode", False), state.get("query_fp_dict"))
        return finalize(state, result, candidate_ids=state.get("candidate_ids", []), results_returned=[],
                         sources_cited=[], no_confident_match=True, degraded_mode=state.get("degraded_mode", False))

    async def assemble_top_match_node(state: PipelineState) -> dict:
        ranked = state["ranked"]
        candidates = state["candidates"]
        ranked_matters_out = [
            {
                "matter_id": r.matter_id, "rank": r.rank, "similarity_rationale": r.similarity_rationale,
                "confidence": r.confidence,
                **{k: v for k, v in next((c for c in candidates if c["matter_id"] == r.matter_id), {}).items()
                   if k in ("title", "client_name", "practice_area", "jurisdiction")},
            }
            for r in sorted(ranked.results, key=lambda r: r.rank)
        ]
        top = ranked_matters_out[0]
        top_matter_id = top["matter_id"]
        return {
            "ranked_matters_out": ranked_matters_out,
            "top": top,
            "top_matter_id": top_matter_id,
            "documents": _document_payload(db, top_matter_id),
            "authorities": _matter_authorities(db, top_matter_id),
        }

    async def comparison_node(state: PipelineState) -> dict:
        try:
            comparison_result = await run_comparison_agent(
                state["query_text"], state["query_fp"], state["top"]["title"], state["documents"]
            )
            return {"comparison": comparison_result.model_dump()}
        except AgentError as exc:
            logger.warning("comparison agent unavailable: %s", exc)
            return {"comparison": None, "degraded_mode": True}

    async def reusability_node(state: PipelineState) -> dict:
        try:
            reusability_result = await run_reusability_agent(state["query_text"], state["top"]["title"], state["documents"])
            return {"reusability": reusability_result.model_dump()}
        except AgentError as exc:
            logger.warning("reusability agent unavailable: %s", exc)
            return {"reusability": None, "degraded_mode": True}

    async def reliability_node(state: PipelineState) -> dict:
        top_matter_id = state["top_matter_id"]
        documents = state["documents"]
        reliability_outcomes = []
        degraded = False

        for auth in state["authorities"]:
            if not auth["relied_upon_for"]:
                continue
            try:
                assessment = await run_reliability_agent(auth["citation"], auth["relied_upon_for"], documents)
                row = ReliabilityAssessment(
                    matter_id=top_matter_id, authority_id=auth["authority_id"], verdict=assessment.verdict,
                    blocked_by_guardrail=False, guardrail_failure_reasons=[], reasoning=assessment.reasoning,
                    points_needing_fresh_work=[p.model_dump() for p in assessment.points_needing_fresh_work],
                    sources=[s.model_dump() for s in assessment.sources], needs_review=True,
                )
                db.add(row)
                db.flush()
                reliability_outcomes.append({
                    "reliability_assessment_id": str(row.id),
                    "authority_id": auth["authority_id"], "citation": auth["citation"],
                    "court": auth["court"], "year": auth["year"], "relied_upon_for": auth["relied_upon_for"],
                    "blocked_by_guardrail": False, "guardrail_failure_reasons": [],
                    "verdict": assessment.verdict, "monitoring_status": assessment.monitoring_status,
                    "reasoning": assessment.reasoning,
                    "points_needing_fresh_work": [p.model_dump() for p in assessment.points_needing_fresh_work],
                    "sources": [s.model_dump() for s in assessment.sources],
                    "needs_review": True, "reviewed_by_user_id": None, "reviewed_at": None,
                })
            except GuardrailTripwireTriggered as exc:
                failures = exc.failures
                row = ReliabilityAssessment(
                    matter_id=top_matter_id, authority_id=auth["authority_id"], verdict=None,
                    blocked_by_guardrail=True, guardrail_failure_reasons=failures,
                    reasoning="Verification failed - result withheld pending manual check.",
                    points_needing_fresh_work=[], sources=[], needs_review=True,
                )
                db.add(row)
                db.flush()
                reliability_outcomes.append({
                    "reliability_assessment_id": str(row.id),
                    "authority_id": auth["authority_id"], "citation": auth["citation"],
                    "court": auth["court"], "year": auth["year"], "relied_upon_for": auth["relied_upon_for"],
                    "blocked_by_guardrail": True, "guardrail_failure_reasons": failures,
                    "verdict": None, "monitoring_status": None,
                    "reasoning": "Verification failed - result withheld pending manual check.",
                    "points_needing_fresh_work": [], "sources": [],
                    "needs_review": True, "reviewed_by_user_id": None, "reviewed_at": None,
                })
            except AgentError as exc:
                logger.warning("reliability agent unavailable for %s: %s", auth["citation"], exc)
                degraded = True

        update: dict = {"reliability_outcomes": reliability_outcomes}
        if degraded:
            update["degraded_mode"] = True
        return update

    async def finalize_success_node(state: PipelineState) -> dict:
        comparison = state.get("comparison")
        result = {
            "no_confident_match": False,
            "rationale": state["ranked"].rationale,
            "degraded_mode": state.get("degraded_mode", False),
            "query_fingerprint": state.get("query_fp_dict"),
            "ranked_matters": state["ranked_matters_out"],
            "top_matter": {
                "matter_id": state["top_matter_id"], "title": state["top"]["title"],
                "documents": state["documents"], "authorities": state["authorities"],
            },
            "comparison": comparison,
            "reusability": state.get("reusability"),
            "reliability": state.get("reliability_outcomes", []),
        }
        sources_cited = []
        if comparison:
            sources_cited += [p["source_ref"] for p in comparison.get("similarities", []) + comparison.get("differences", [])]
        return finalize(
            state, result, candidate_ids=state.get("candidate_ids", []),
            results_returned=[{"matter_id": m["matter_id"], "rank": m["rank"]} for m in state["ranked_matters_out"]],
            sources_cited=sources_cited, no_confident_match=False, degraded_mode=state.get("degraded_mode", False),
        )

    graph = StateGraph(PipelineState)
    graph.add_node("fingerprint", fingerprint_node)
    graph.add_node("finalize_no_fingerprint", finalize_no_fingerprint_node)
    graph.add_node("retrieve_candidates", retrieve_candidates_node)
    graph.add_node("finalize_no_candidates", finalize_no_candidates_node)
    graph.add_node("retrieval_rank", retrieval_rank_node)
    graph.add_node("finalize_retrieval_failed", finalize_retrieval_failed_node)
    graph.add_node("finalize_no_confident_match", finalize_no_confident_match_node)
    graph.add_node("assemble_top_match", assemble_top_match_node)
    graph.add_node("comparison", comparison_node)
    graph.add_node("reusability", reusability_node)
    graph.add_node("reliability", reliability_node)
    graph.add_node("finalize_success", finalize_success_node)

    graph.set_entry_point("fingerprint")
    graph.add_conditional_edges("fingerprint", route_after_fingerprint,
                                 {"no_fingerprint": "finalize_no_fingerprint", "continue": "retrieve_candidates"})
    graph.add_edge("finalize_no_fingerprint", END)

    graph.add_conditional_edges("retrieve_candidates", route_after_candidates,
                                 {"no_candidates": "finalize_no_candidates", "continue": "retrieval_rank"})
    graph.add_edge("finalize_no_candidates", END)

    graph.add_conditional_edges(
        "retrieval_rank", route_after_retrieval,
        {"retrieval_failed": "finalize_retrieval_failed", "no_confident_match": "finalize_no_confident_match",
         "continue": "assemble_top_match"},
    )
    graph.add_edge("finalize_retrieval_failed", END)
    graph.add_edge("finalize_no_confident_match", END)

    graph.add_edge("assemble_top_match", "comparison")
    graph.add_edge("comparison", "reusability")
    graph.add_edge("reusability", "reliability")
    graph.add_edge("reliability", "finalize_success")
    graph.add_edge("finalize_success", END)

    return graph.compile()


async def run_query_pipeline(db: Session, user_id: str, query_text: str, source: str = "web") -> dict:
    with trace("second_brain_query_pipeline"):
        graph = _build_graph(db)
        initial_state: PipelineState = {
            "query_text": query_text, "source": source, "user_id": user_id, "degraded_mode": False,
        }
        final_state = await graph.ainvoke(initial_state)
        return final_state["result"]

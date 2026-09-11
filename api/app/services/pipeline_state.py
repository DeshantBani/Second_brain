"""Shared state for the query pipeline's LangGraph. A plain TypedDict (no custom
reducers needed) - every node returns a partial dict of the keys it sets, and
LangGraph merges them into this state as the graph runs. There is no fan-out/parallel
writes to the same key anywhere in this graph, so "last write wins" per key (the
default merge behavior) is exactly right - no Annotated/reducer machinery needed."""
from typing import TypedDict

from app.agents_sdk.schemas import IssueFingerprintSchema, RetrievalResult


class PipelineState(TypedDict, total=False):
    # Set at entry
    query_text: str
    source: str
    user_id: str

    # Accumulates as nodes run
    degraded_mode: bool
    query_fp: IssueFingerprintSchema | None
    query_fp_dict: dict | None
    candidate_ids: list[str]
    candidates: list[dict]
    ranked: RetrievalResult | None
    retrieval_failed: bool
    ranked_matters_out: list[dict]
    top: dict
    top_matter_id: str
    documents: list[dict]
    authorities: list[dict]
    comparison: dict | None
    reusability: dict | None
    reliability_outcomes: list[dict]

    # Set only by a finalize_* node - the graph's actual output
    result: dict

"""Standalone verification CLI, used during the build to sanity-check the fingerprint
and retrieval agents against seeded data without going through the full HTTP stack.

Usage (inside the api container):
    python -m app.scripts.try_fingerprint "Our client wants to exit a five year..."
"""
import asyncio
import sys

from sqlalchemy import select

from app.agents_sdk.fingerprint_agent import run_fingerprint_agent
from app.agents_sdk.retrieval_agent import run_retrieval_agent
from app.db import OwnerSessionLocal
from app.models.fingerprint import IssueFingerprint
from app.models.matter import Matter
from app.services.embeddings import embed_text
from app.services.fingerprint_text import fingerprint_to_embedding_text


async def main(query_text: str):
    fp = await run_fingerprint_agent(query_text)
    print("=== Fingerprint ===")
    print(fp.model_dump_json(indent=2))

    vector = embed_text(fingerprint_to_embedding_text(fp))
    print(f"\nembedding: {'ok, dim=' + str(len(vector)) if vector else 'unavailable (degraded mode)'}")

    db = OwnerSessionLocal()
    try:
        rows = db.execute(select(Matter, IssueFingerprint).join(IssueFingerprint, IssueFingerprint.matter_id == Matter.id)).all()
        candidates = [
            {
                "matter_id": str(m.id), "title": m.title,
                "fingerprint": {
                    "jurisdiction": f.jurisdiction, "practice_area": f.practice_area,
                    "procedural_posture": f.procedural_posture, "factual_pattern": f.factual_pattern,
                    "contract_clauses": f.contract_clauses, "clause_tags": f.clause_tags, "summary": f.summary,
                },
            }
            for m, f in rows
        ]
        print(f"\n=== {len(candidates)} candidates in archive ===")
        ranked = await run_retrieval_agent(fp, candidates)
        print(ranked.model_dump_json(indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else (
        "Our client wants to exit a five year manufacturing supply agreement governed by Indian law. "
        "The contract has a termination for convenience clause with a thirty day cure period. Counterparty "
        "is threatening damages. Have we advised on this before?"
    )
    asyncio.run(main(query))

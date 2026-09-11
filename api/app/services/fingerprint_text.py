from app.agents_sdk.schemas import IssueFingerprintSchema


def fingerprint_to_embedding_text(fp: IssueFingerprintSchema) -> str:
    """Flatten a fingerprint into the text we actually embed. Kept in one place so the
    ingestion pipeline (per-matter fingerprints) and the live query path embed
    fingerprints identically - otherwise vector similarity would be comparing apples
    to oranges."""
    clause_bits = "; ".join(
        f"{c.clause_type}: {c.key_terms}" for c in fp.contract_clauses if c.exists
    )
    return "\n".join(
        [
            f"Jurisdiction: {fp.jurisdiction}",
            f"Practice area: {fp.practice_area}",
            f"Matter type: {fp.matter_type}",
            f"Procedural posture: {fp.procedural_posture}",
            f"Factual pattern: {fp.factual_pattern}",
            f"Contract clauses: {clause_bits}",
            f"Tags: {', '.join(fp.clause_tags)}",
            f"Summary: {fp.summary}",
        ]
    )

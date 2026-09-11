"""Shared grounding-verification helper: is a quote an agent produced actually present
in a given source text? Used by citation_guardrail.py (verifying the reliability
agent's provider-sourced quotes) and services/matter_intake.py (verifying the
citation-extraction agent's document quotes) - anywhere an agent claims to be quoting
something verbatim and that claim needs to be checked before it's trusted."""


def _normalize(text: str) -> set[str]:
    return {w.strip(".,;:()\"'") for w in text.lower().split() if w.strip(".,;:()\"'")}


def fuzzy_contains(haystack: str, needle: str, threshold: float = 0.6) -> bool:
    """True if `needle` appears verbatim in `haystack`, or if enough of its words do
    (case-insensitive) to treat it as a genuine paraphrase-safe match rather than a
    fabricated quote."""
    if not needle.strip():
        return False
    haystack_l = haystack.lower()
    if needle.lower() in haystack_l:
        return True
    needle_words = _normalize(needle)
    if not needle_words:
        return False
    haystack_words = _normalize(haystack)
    overlap = len(needle_words & haystack_words)
    return (overlap / len(needle_words)) >= threshold

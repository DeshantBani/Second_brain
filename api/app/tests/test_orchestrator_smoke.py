"""Thin smoke tests: the full pipeline needs a live Postgres + Gemini key to run for
real (see the Section 15 curl-based verification in the build plan) - what we can and
should unit-test without that is that the module wires up cleanly, and that the pure
helper functions behave correctly."""
from app.agents_sdk.client import GuardrailTripwireTriggered
from app.services.ingestion import parse_page_map


def test_orchestrator_module_imports_cleanly():
    import app.services.orchestrator  # noqa: F401


def test_parse_page_map_with_explicit_page_markers():
    text = (
        "## PAGE 1\n"
        "First paragraph.\n\n"
        "Second paragraph.\n"
        "## PAGE 2\n"
        "Third paragraph on page two."
    )
    page_map = parse_page_map(text)
    assert page_map == [
        {"page": 1, "paragraph": 1, "text": "First paragraph."},
        {"page": 1, "paragraph": 2, "text": "Second paragraph."},
        {"page": 2, "paragraph": 1, "text": "Third paragraph on page two."},
    ]


def test_parse_page_map_without_markers_falls_back_to_single_page():
    text = "Only paragraph one.\n\nOnly paragraph two."
    page_map = parse_page_map(text)
    assert page_map == [
        {"page": 1, "paragraph": 1, "text": "Only paragraph one."},
        {"page": 1, "paragraph": 2, "text": "Only paragraph two."},
    ]


def test_guardrail_tripwire_triggered_carries_failures():
    exc = GuardrailTripwireTriggered(["bad citation status"])
    assert exc.failures == ["bad citation status"]
    assert "bad citation status" in str(exc)

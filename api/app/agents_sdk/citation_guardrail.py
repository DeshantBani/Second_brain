"""The citation verification guardrail: the safety margin against a false "green" (or
a false anything). Runs after the reliability agent drafts its verdict, with visibility
only into the CaseLawProvider data (not the reasoning that produced the draft), and
checks every claim it can. A single failure trips the tripwire and BLOCKS the result -
see agents_sdk/client.py's GuardrailTripwireTriggered and orchestrator.py's handling of
that exception."""
from app.agents_sdk.client import GuardrailFunctionOutput
from app.agents_sdk.schemas import ReliabilityAssessmentSchema
from app.reliability.factory import get_case_law_provider


def _normalize(text: str) -> set[str]:
    return {w.strip(".,;:()\"'") for w in text.lower().split() if w.strip(".,;:()\"'")}


def _fuzzy_contains(haystack: str, needle: str, threshold: float = 0.6) -> bool:
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


async def check_reliability_output(output: ReliabilityAssessmentSchema) -> GuardrailFunctionOutput:
    """The actual verification logic. Called directly by reliability_agent.py after
    generation, and by tests - a plain async function, not tied to any agent
    framework's decorator machinery."""
    failures: list[str] = []
    provider = get_case_law_provider()

    for source in output.sources:
        try:
            live_status = provider.get_citation_status(source.citation)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Could not re-verify citation status for '{source.citation}': {exc}")
            continue

        if live_status.status != source.status:
            failures.append(
                f"Citation status mismatch for '{source.citation}': assessment says "
                f"'{source.status}' but the provider currently reports '{live_status.status}'."
            )

        # The quoted treatment_excerpt must actually appear in what the provider returned -
        # either the citation's own treatment history, or (less strictly) be grounded text,
        # never a fabricated quote.
        provider_texts = [event.excerpt for event in live_status.treatment_history]
        if provider_texts and not any(_fuzzy_contains(t, source.treatment_excerpt) for t in provider_texts):
            failures.append(
                f"Unverifiable treatment_excerpt for '{source.citation}': the quoted text does not match "
                "any treatment record returned by the CaseLawProvider."
            )

    if output.verdict == "green" and output.monitoring_status == "checked_flagged":
        failures.append("Internal inconsistency: verdict is 'green' but monitoring_status is 'checked_flagged'.")

    return GuardrailFunctionOutput(
        output_info={"failures": failures},
        tripwire_triggered=bool(failures),
    )

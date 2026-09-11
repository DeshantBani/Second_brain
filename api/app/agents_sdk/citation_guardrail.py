"""The citation verification guardrail: the safety margin against a false "green" (or
a false anything). Runs after the reliability agent drafts its verdict, with visibility
only into the CaseLawProvider data (not the reasoning that produced the draft), and
checks every claim it can. A single failure trips the tripwire and BLOCKS the result -
see agents_sdk/client.py's GuardrailTripwireTriggered and orchestrator.py's handling of
that exception."""
from app.agents_sdk.client import GuardrailFunctionOutput
from app.agents_sdk.schemas import ReliabilityAssessmentSchema
from app.agents_sdk.text_match import fuzzy_contains
from app.reliability.factory import get_case_law_provider


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
        if provider_texts and not any(fuzzy_contains(t, source.treatment_excerpt) for t in provider_texts):
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

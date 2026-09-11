"""Static reference data shared across agent prompts. Previously exposed as
SDK-specific "function tools" (get_taxonomy, fetch_document_span, etc.) - now that
every agent call is a single structured-output generation with all needed context
already embedded in the prompt (see client.py's docstring for why), these are just
plain constants/helpers imported directly by the agent modules that need them."""

TAXONOMY = {
    "jurisdictions": [
        "India", "India - Maharashtra", "India - Karnataka", "India - Delhi", "India - Gujarat",
    ],
    "practice_areas": [
        "commercial_contracts", "employment", "arbitration", "real_estate",
        "corporate_advisory", "due_diligence",
    ],
    "clause_tags": [
        "termination_for_convenience", "termination_for_cause", "cure_period",
        "supply_agreement", "distribution_agreement", "limitation_of_liability",
        "damages", "arbitration_clause", "epc_contract", "confidentiality",
    ],
}

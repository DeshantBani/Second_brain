"""Stub for the real Indian Kanoon integration - signatures and documented shape only.

Target: api.indiankanoon.org, token-based auth via `Authorization: Token <INDIANKANOON_API_TOKEN>`.
Indian Kanoon's documented Precedent Analyser classifies each citation within a judgment
as Party / Neutral / Positive / Negative, plus citing/cited-by relationships - that
classification is meant to be used directly as the factual basis for AuthorityStatus,
never inferred by an LLM.

No HTTP calls are implemented in this pass (access hasn't been arranged yet). The
moment a real INDIANKANOON_API_TOKEN exists, implement the two methods below against
these documented endpoints and re-run the Section 15 QA scenario against live data -
a reliability engine validated only against MockCaseLawProvider fixtures hasn't
actually been validated.
"""
from app.reliability.provider import AuthorityStatus, CaseLawProvider, Judgment


class IndianKanoonProvider(CaseLawProvider):
    def __init__(self, api_token: str, base_url: str = "https://api.indiankanoon.org"):
        self.api_token = api_token
        self.base_url = base_url
        self._headers = {"Authorization": f"Token {api_token}"}

    def get_citation_status(self, citation: str) -> AuthorityStatus:
        # Intended shape: look up the judgment, run it through the Precedent Analyser,
        # map the aggregate Party/Neutral/Positive/Negative classification of citing
        # judgments onto our good_law/doubted/distinguished/overruled status enum.
        raise NotImplementedError(
            "IndianKanoonProvider.get_citation_status: live integration not implemented in this pass. "
            "Set CASE_LAW_PROVIDER=mock until INDIANKANOON_API_TOKEN access is arranged."
        )

    def get_citing_judgments(self, citation: str) -> list[Judgment]:
        # Intended shape: GET the citation's citedbyjudgments from the Precedent
        # Analyser, mapping each result's classification directly to Judgment.treatment.
        raise NotImplementedError(
            "IndianKanoonProvider.get_citing_judgments: live integration not implemented in this pass. "
            "Set CASE_LAW_PROVIDER=mock until INDIANKANOON_API_TOKEN access is arranged."
        )

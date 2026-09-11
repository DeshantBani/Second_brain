"""Fixture-backed CaseLawProvider. Built first, deliberately, so the reliability agent,
the citation-verification guardrail, the background monitor job, and the Section 15 QA
scenario can all be exercised end-to-end before any real Indian Kanoon access exists.

Fixtures live in db/seed/fixtures/case_law/fixtures.json and include one genuine
negative-treatment record (Continental Constructions, distinguished by Bharat Heavy
Fabrications) so a real amber verdict is reachable without a live API.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.reliability.provider import AuthorityStatus, CaseLawProvider, Judgment, TreatmentEvent

def _locate_fixtures_path() -> Path:
    """The repo is laid out as `<root>/api/app/...` in local dev but flattened to
    `/app/app/...` inside the api Docker image (build context is ./api), with
    `./db` volume-mounted at `/app/db` at runtime - so `db/` sits one directory level
    higher relative to this file in the container than it does locally. Rather than
    hardcode one, try both known-good relative locations."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "db" / "seed" / "fixtures" / "case_law" / "fixtures.json",  # docker: /app/db/...
        here.parents[3] / "db" / "seed" / "fixtures" / "case_law" / "fixtures.json",  # local dev: <repo>/db/...
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate db/seed/fixtures/case_law/fixtures.json in any expected location: "
        + ", ".join(str(c) for c in candidates)
    )


FIXTURES_PATH = _locate_fixtures_path()


class MockCaseLawProvider(CaseLawProvider):
    def __init__(self, fixtures_path: Path = FIXTURES_PATH):
        with open(fixtures_path, encoding="utf-8") as f:
            records = json.load(f)
        self._by_citation: dict[str, dict] = {r["citation"]: r for r in records}

    def get_citation_status(self, citation: str) -> AuthorityStatus:
        record = self._by_citation.get(citation)
        if record is None:
            # Unknown citation: neither good_law nor overruled - "doubted" is the
            # honest default for "we have no fixture data on this," never a fabricated green.
            return AuthorityStatus(
                citation=citation,
                status="doubted",
                treatment_history=[],
                checked_at=datetime.now(timezone.utc),
            )
        events = [
            TreatmentEvent(
                citing_case=j["citing_case"],
                court=j["court"],
                year=j["year"],
                treatment=j["treatment"],
                excerpt=j["excerpt"],
            )
            for j in record.get("citing_judgments", [])
        ]
        return AuthorityStatus(
            citation=record["citation"],
            status=record["status"],
            treatment_history=events,
            checked_at=datetime.now(timezone.utc),
        )

    def get_citing_judgments(self, citation: str) -> list[Judgment]:
        record = self._by_citation.get(citation)
        if record is None:
            return []
        return [
            Judgment(
                citation=j["citing_case"],
                court=j["court"],
                year=j["year"],
                treatment=j["treatment"],
                excerpt=j["excerpt"],
            )
            for j in record.get("citing_judgments", [])
        ]

    def get_holding_excerpt(self, citation: str) -> str:
        """Not part of the CaseLawProvider ABC - a mock-only convenience used by the
        seed script to store a citation's original holding text."""
        record = self._by_citation.get(citation)
        return record["holding_excerpt"] if record else ""

    def all_citations(self) -> list[str]:
        return list(self._by_citation.keys())

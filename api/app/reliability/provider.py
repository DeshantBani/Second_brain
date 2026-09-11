"""The CaseLawProvider abstraction. This is the single seam between "what the
reliability agent believes about case law" and "where that belief actually comes from."

Non-negotiable: no agent or business logic outside this package may branch on which
concrete provider is active. Only `factory.get_case_law_provider()` may be imported
elsewhere - see factory.py.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TreatmentLabel = Literal["good_law", "doubted", "distinguished", "overruled"]


class TreatmentEvent(BaseModel):
    citing_case: str
    court: str
    year: int
    treatment: Literal["party", "neutral", "positive", "negative"]
    excerpt: str


class AuthorityStatus(BaseModel):
    citation: str
    status: TreatmentLabel
    treatment_history: list[TreatmentEvent]
    checked_at: datetime


class Judgment(BaseModel):
    citation: str
    court: str
    year: int
    treatment: Literal["party", "neutral", "positive", "negative"]
    excerpt: str


class CaseLawProvider(ABC):
    """Behind this interface: a live legal-data source, or fixtures. Nothing else
    should know or care which."""

    @abstractmethod
    def get_citation_status(self, citation: str) -> AuthorityStatus:
        """Return the current authoritative status of a citation."""
        raise NotImplementedError

    @abstractmethod
    def get_citing_judgments(self, citation: str) -> list[Judgment]:
        """Return judgments that have cited this authority, with their treatment."""
        raise NotImplementedError

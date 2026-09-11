from datetime import date, datetime

from pydantic import BaseModel, field_validator


class MatterSummary(BaseModel):
    id: str
    title: str
    client_name: str
    practice_area: str
    jurisdiction: str
    matter_type: str
    status: str
    opened_date: date | None = None

    model_config = {"from_attributes": True}

    # SQLAlchemy/psycopg3 hand back uuid.UUID objects for UUID columns, not str -
    # coerce here so model_validate(orm_object) doesn't choke on the type mismatch.
    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)


class DocumentSummary(BaseModel):
    id: str
    title: str
    doc_type: str
    confidentiality_tier: str
    mime_type: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)


class DocumentDetail(DocumentSummary):
    extracted_text: str
    page_map: list


class AuthorityRef(BaseModel):
    id: str
    citation: str
    court: str
    year: int
    status: str
    monitoring_status: str
    relied_upon_for: str
    cited_at_page: int
    cited_at_paragraph: int


class FingerprintOut(BaseModel):
    id: str
    jurisdiction: str
    practice_area: str
    procedural_posture: str
    factual_pattern: dict
    contract_clauses: dict
    clause_tags: list[str]
    summary: str

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v):
        return str(v)


class MatterDetail(MatterSummary):
    documents: list[DocumentSummary] = []
    authorities: list[AuthorityRef] = []
    fingerprint: FingerprintOut | None = None

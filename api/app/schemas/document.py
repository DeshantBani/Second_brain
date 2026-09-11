from pydantic import BaseModel


class IngestDocumentRequest(BaseModel):
    matter_id: str
    title: str
    doc_type: str
    confidentiality_tier: str = "tier1_confidential"
    text: str  # raw extracted text; clean digital text only for this pass (no OCR)


class LinkedCitationOut(BaseModel):
    citation: str
    status: str
    is_new_authority: bool


class IngestDocumentResponse(BaseModel):
    document_id: str
    fingerprint_id: str | None = None
    degraded_mode: bool = False
    citations_linked: list[LinkedCitationOut] = []


class CreateMatterRequest(BaseModel):
    title: str
    client_name: str
    doc_title: str = "Ingested Report"
    doc_type: str = "memo"
    confidentiality_tier: str = "tier1_confidential"
    opened_date: str | None = None  # ISO date string, optional
    raw_text: str


class CreateMatterResponse(BaseModel):
    matter_id: str
    document_id: str
    degraded_mode: bool
    jurisdiction: str | None
    practice_area: str | None
    matter_type: str | None
    citations_linked: list[LinkedCitationOut] = []

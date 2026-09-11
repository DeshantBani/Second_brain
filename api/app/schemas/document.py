from pydantic import BaseModel


class IngestDocumentRequest(BaseModel):
    matter_id: str
    title: str
    doc_type: str
    confidentiality_tier: str = "tier1_confidential"
    text: str  # raw extracted text; clean digital text only for this pass (no OCR)


class IngestDocumentResponse(BaseModel):
    document_id: str
    fingerprint_id: str | None = None
    degraded_mode: bool = False

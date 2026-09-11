from datetime import datetime

from pydantic import BaseModel


class ConversationTurn(BaseModel):
    role: str  # "assistant" | "user"
    content: str
    at: str


class CreateDraftingSessionRequest(BaseModel):
    case_brief: str


class AddDraftingMessageRequest(BaseModel):
    message: str


class PetitionSectionOut(BaseModel):
    name: str
    description: str


class TemplateStructureOut(BaseModel):
    sections: list[PetitionSectionOut]
    grounded_in_sources: bool
    notes: str


class DraftedSectionOut(BaseModel):
    section_name: str
    content: str


class DraftingSessionOut(BaseModel):
    id: str
    case_brief: str
    status: str
    conversation: list[ConversationTurn]
    gathered_requirements: dict | None
    template_structure: dict | None
    draft_sections: list[DraftedSectionOut] | None
    degraded_mode: bool
    created_at: datetime
    updated_at: datetime


class DraftingSessionSummary(BaseModel):
    id: str
    case_brief: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProofreadRequest(BaseModel):
    draft_text: str
    case_brief: str | None = None


class ProofreadingFindingOut(BaseModel):
    category: str
    severity: str
    section: str
    issue: str
    suggestion: str
    grounding_excerpt: str


class ProofreadingReportOut(BaseModel):
    id: str
    case_brief: str | None
    draft_text: str
    summary: str
    findings: list[ProofreadingFindingOut]
    degraded_mode: bool
    created_at: datetime


class ProofreadingReportSummary(BaseModel):
    id: str
    summary: str
    finding_count: int
    created_at: datetime

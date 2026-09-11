export interface MeResponse {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
}

export interface MatterSummary {
  id: string;
  title: string;
  client_name: string;
  practice_area: string;
  jurisdiction: string;
  matter_type: string;
  status: string;
  opened_date: string | null;
}

export interface DocumentSummary {
  id: string;
  title: string;
  doc_type: string;
  confidentiality_tier: string;
  mime_type: string;
  created_at: string;
}

export interface DocumentDetail extends DocumentSummary {
  extracted_text: string;
  page_map: { page: number; paragraph: number; text: string }[];
}

export interface AuthorityRef {
  id: string;
  citation: string;
  court: string;
  year: number;
  status: string;
  monitoring_status: string;
  relied_upon_for: string;
  cited_at_page: number;
  cited_at_paragraph: number;
}

export interface FingerprintOut {
  id: string;
  jurisdiction: string;
  practice_area: string;
  procedural_posture: string;
  factual_pattern: Record<string, unknown>;
  contract_clauses: Record<string, unknown>;
  clause_tags: string[];
  summary: string;
}

export interface MatterDetail extends MatterSummary {
  documents: DocumentSummary[];
  authorities: AuthorityRef[];
  fingerprint: FingerprintOut | null;
}

export interface LinkedCitationOut {
  citation: string;
  status: string;
  is_new_authority: boolean;
}

export interface CreateMatterRequest {
  title: string;
  client_name: string;
  doc_title?: string;
  doc_type?: string;
  confidentiality_tier?: string;
  opened_date?: string | null;
  raw_text: string;
}

export interface CreateMatterResponse {
  matter_id: string;
  document_id: string;
  degraded_mode: boolean;
  jurisdiction: string | null;
  practice_area: string | null;
  matter_type: string | null;
  citations_linked: LinkedCitationOut[];
}

export interface IngestDocumentRequest {
  matter_id: string;
  title: string;
  doc_type: string;
  confidentiality_tier?: string;
  text: string;
}

export interface IngestDocumentResponse {
  document_id: string;
  fingerprint_id: string | null;
  degraded_mode: boolean;
  citations_linked: LinkedCitationOut[];
}

export interface SourceRef {
  document_id: string;
  page: number;
  paragraph: number;
  quote: string;
}

export interface ComparisonPoint {
  point: string;
  source_ref: SourceRef;
}

export interface DifferencePoint extends ComparisonPoint {
  materiality: "material" | "minor";
}

export interface ComparisonResult {
  summary: string;
  similarities: ComparisonPoint[];
  differences: DifferencePoint[];
  flags: string[];
}

export interface ReusabilityComponent {
  component: "reasoning" | "research" | "drafting_language" | "argument_structure" | "authorities";
  reusability: "fully_reusable" | "adapt_required" | "not_reusable";
  notes: string;
  source_ref: SourceRef;
}

export interface ReusabilityBreakdown {
  components: ReusabilityComponent[];
}

export interface RankedMatterOut {
  matter_id: string;
  title: string;
  client_name: string;
  practice_area: string;
  jurisdiction: string;
  rank: number;
  similarity_rationale: string;
  confidence: "high" | "medium" | "low";
}

export interface ReliabilityOutcomeOut {
  reliability_assessment_id: string | null;
  authority_id: string;
  citation: string;
  court: string;
  year: number;
  relied_upon_for: string;
  blocked_by_guardrail: boolean;
  guardrail_failure_reasons: string[];
  verdict: "green" | "amber" | "red" | null;
  monitoring_status: "checked_clear" | "checked_flagged" | null;
  reasoning: string | null;
  points_needing_fresh_work: { point: string; source_ref: SourceRef }[];
  sources: { citation: string; status: string; treatment_excerpt: string }[];
  needs_review: boolean;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
}

export interface QueryPageMapEntry {
  page: number;
  paragraph: number;
  text: string;
}

export interface QueryTopMatterDocument {
  id: string;
  title: string;
  doc_type: string;
  page_map: QueryPageMapEntry[];
}

export interface QueryTopMatterAuthority {
  matter_authority_id: string;
  authority_id: string;
  citation: string;
  court: string;
  year: number;
  relied_upon_for: string;
  cited_in_document_id: string;
  cited_at_page: number;
  cited_at_paragraph: number;
}

export interface QueryResultOut {
  query_log_id: string;
  query_text: string;
  no_confident_match: boolean;
  rationale: string;
  degraded_mode: boolean;
  replayed_from_cache: boolean;
  query_fingerprint: Record<string, unknown> | null;
  ranked_matters: RankedMatterOut[];
  top_matter: { matter_id: string; title: string; documents: QueryTopMatterDocument[]; authorities: QueryTopMatterAuthority[] } | null;
  comparison: ComparisonResult | null;
  reusability: ReusabilityBreakdown | null;
  reliability: ReliabilityOutcomeOut[];
}

export interface AuthorityOut {
  id: string;
  citation: string;
  court: string;
  year: number;
  status: string;
  monitoring_status: string;
  last_checked_at: string | null;
  provider_source: string;
  treatment_history: unknown[];
}

export interface AuditLogOut {
  id: string;
  pipeline_run_id: string | null;
  user_email: string;
  source: string;
  query_text: string;
  no_confident_match: boolean;
  degraded_mode: boolean;
  replayed_from_cache: boolean;
  blocked_by_guardrail: boolean;
  created_at: string;
}

export interface HealthOut {
  status: string;
  llm_configured: boolean;
  llm_provider: string;
  case_law_provider: string;
  db_ok: boolean;
}

export interface QueryHistoryItem {
  query_log_id: string;
  query_text: string;
  source: string;
  no_confident_match: boolean;
  degraded_mode: boolean;
  replayed_from_cache: boolean;
  blocked_by_guardrail: boolean;
  created_at: string;
}

export interface AgentCallLogOut {
  id: string;
  pipeline_run_id: string | null;
  agent_name: string;
  model: string;
  cache_key: string;
  system_instruction: string;
  user_content: string;
  raw_response_text: string | null;
  success: boolean;
  replayed_from_cache: boolean;
  error_message: string | null;
  duration_ms: number;
  created_at: string;
}

// --- Drafting ---

export interface ConversationTurn {
  role: "assistant" | "user";
  content: string;
  at: string;
}

export interface GatheredRequirements {
  petition_type: string;
  forum: string;
  petitioner: string;
  respondent: string;
  grounds: string[];
  relief_sought: string;
  key_facts_summary: string;
}

export interface PetitionSectionOut {
  name: string;
  description: string;
}

export interface TemplateStructureOut {
  sections: PetitionSectionOut[];
  grounded_in_sources: boolean;
  notes: string;
}

export interface DraftedSectionOut {
  section_name: string;
  content: string;
}

export interface DraftingSessionOut {
  id: string;
  case_brief: string;
  status: "gathering" | "ready" | "drafted";
  conversation: ConversationTurn[];
  gathered_requirements: GatheredRequirements | null;
  template_structure: TemplateStructureOut | null;
  draft_sections: DraftedSectionOut[] | null;
  degraded_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface DraftingSessionSummary {
  id: string;
  case_brief: string;
  status: "gathering" | "ready" | "drafted";
  created_at: string;
  updated_at: string;
}

// --- Proofreading ---

export interface ProofreadingFindingOut {
  category: "format" | "content" | "missing_fact";
  severity: "high" | "medium" | "low";
  section: string;
  issue: string;
  suggestion: string;
  grounding_excerpt: string;
}

export interface ProofreadingReportOut {
  id: string;
  case_brief: string | null;
  draft_text: string;
  summary: string;
  findings: ProofreadingFindingOut[];
  degraded_mode: boolean;
  created_at: string;
}

export interface ProofreadingReportSummary {
  id: string;
  summary: string;
  finding_count: number;
  created_at: string;
}

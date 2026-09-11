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
  user_email: string;
  source: string;
  query_text: string;
  no_confident_match: boolean;
  degraded_mode: boolean;
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

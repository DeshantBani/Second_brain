import { getToken } from "./auth";
import type {
  AgentCallLogOut,
  AuditLogOut,
  AuthorityOut,
  CreateMatterRequest,
  CreateMatterResponse,
  DraftingSessionOut,
  DraftingSessionSummary,
  HealthOut,
  IngestDocumentRequest,
  IngestDocumentResponse,
  MatterDetail,
  MatterSummary,
  MeResponse,
  ProofreadingReportOut,
  ProofreadingReportSummary,
  QueryHistoryItem,
  QueryResultOut,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // response body wasn't JSON - fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function requestFormData<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  // deliberately no Content-Type here - the browser sets the multipart boundary itself
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export interface ExtractTextResponse {
  filename: string;
  text: string;
  truncated: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  display_name: string;
  role: string;
}

export const api = {
  health: () => request<HealthOut>("/health"),

  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  me: () => request<MeResponse>("/auth/me"),

  listMatters: () => request<MatterSummary[]>("/matters"),

  getMatter: (matterId: string) => request<MatterDetail>(`/matters/${matterId}`),

  createMatter: (payload: CreateMatterRequest) =>
    request<CreateMatterResponse>("/matters", { method: "POST", body: JSON.stringify(payload) }),

  getDocument: (matterId: string, documentId: string) =>
    request(`/matters/${matterId}/documents/${documentId}`),

  ingestDocument: (payload: IngestDocumentRequest) =>
    request<IngestDocumentResponse>("/documents", { method: "POST", body: JSON.stringify(payload) }),

  submitQuery: (queryText: string, source: string = "web") =>
    request<QueryResultOut>("/query", { method: "POST", body: JSON.stringify({ query_text: queryText, source }) }),

  getQuery: (queryLogId: string) => request<QueryResultOut>(`/query/${queryLogId}`),

  listQueryHistory: () => request<QueryHistoryItem[]>("/query"),

  reviewAssessment: (queryLogId: string, reliabilityAssessmentId: string, decision: string = "reviewed") =>
    request(`/query/${queryLogId}/review`, {
      method: "POST",
      body: JSON.stringify({ reliability_assessment_id: reliabilityAssessmentId, decision }),
    }),

  listAuthorities: () => request<AuthorityOut[]>("/admin/authorities"),

  recheckAuthority: (authorityId: string) =>
    request(`/admin/authorities/${authorityId}/recheck`, { method: "POST" }),

  listAudit: () => request<AuditLogOut[]>("/admin/audit"),

  listAgentCalls: (params?: { pipeline_run_id?: string; agent_name?: string }) => {
    const qs = new URLSearchParams();
    if (params?.pipeline_run_id) qs.set("pipeline_run_id", params.pipeline_run_id);
    if (params?.agent_name) qs.set("agent_name", params.agent_name);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<AgentCallLogOut[]>(`/admin/agent-calls${suffix}`);
  },

  // --- Drafting ---
  startDraftingSession: (caseBrief: string) =>
    request<DraftingSessionOut>("/drafting/sessions", { method: "POST", body: JSON.stringify({ case_brief: caseBrief }) }),

  listDraftingSessions: () => request<DraftingSessionSummary[]>("/drafting/sessions"),

  getDraftingSession: (sessionId: string) => request<DraftingSessionOut>(`/drafting/sessions/${sessionId}`),

  sendDraftingMessage: (sessionId: string, message: string) =>
    request<DraftingSessionOut>(`/drafting/sessions/${sessionId}/messages`, { method: "POST", body: JSON.stringify({ message }) }),

  generateDraft: (sessionId: string) =>
    request<DraftingSessionOut>(`/drafting/sessions/${sessionId}/draft`, { method: "POST" }),

  // --- Proofreading ---
  proofread: (draftText: string, caseBrief?: string) =>
    request<ProofreadingReportOut>("/proofread", {
      method: "POST",
      body: JSON.stringify({ draft_text: draftText, case_brief: caseBrief || null }),
    }),

  listProofreadingReports: () => request<ProofreadingReportSummary[]>("/proofread"),

  getProofreadingReport: (reportId: string) => request<ProofreadingReportOut>(`/proofread/${reportId}`),

  // --- Uploads ---
  extractText: (file: File, addPageMarkers: boolean = true) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("add_page_markers", String(addPageMarkers));
    return requestFormData<ExtractTextResponse>("/uploads/extract-text", formData);
  },
};

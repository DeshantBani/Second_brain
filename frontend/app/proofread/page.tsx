"use client";

import { FormEvent, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, SearchCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FindingsList } from "@/components/proofread/FindingsList";
import { AgentTraceLoader } from "@/components/query/AgentTraceLoader";
import { DocumentUpload } from "@/components/shared/DocumentUpload";
import { api, ApiError } from "@/lib/api";
import { appendExtractedText, formatDateTime } from "@/lib/format";
import type { ProofreadingReportOut, ProofreadingReportSummary } from "@/lib/types";

export default function ProofreadPage() {
  const [caseBrief, setCaseBrief] = useState("");
  const [draftText, setDraftText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ProofreadingReportOut | null>(null);
  const [recent, setRecent] = useState<ProofreadingReportSummary[] | null>(null);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("proofread_prefill");
      if (raw) {
        const prefill = JSON.parse(raw);
        setDraftText(prefill.draft_text || "");
        setCaseBrief(prefill.case_brief || "");
        sessionStorage.removeItem("proofread_prefill");
      }
    } catch {
      // ignore
    }
    api.listProofreadingReports().then(setRecent).catch(() => setRecent([]));
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setReport(null);
    try {
      const result = await api.proofread(draftText, caseBrief || undefined);
      setReport(result);
      api.listProofreadingReports().then(setRecent).catch(() => {});
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not proofread this draft.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="font-display text-2xl text-ink mb-1.5">Proofread</h1>
        <p className="text-sm text-ink-muted">
          Paste a draft petition/application. Add the case brief too, and the review will also flag any
          material fact from the brief that&apos;s missing from the draft.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-ink-muted mb-1.5">Case brief (optional, but enables missing-fact checks)</label>
          <div className="mb-2">
            <DocumentUpload
              label="Upload case document"
              onExtracted={(text, filename) => setCaseBrief((prev) => appendExtractedText(prev, text, filename))}
            />
          </div>
          <Textarea value={caseBrief} onChange={(e) => setCaseBrief(e.target.value)} rows={4} placeholder="Paste or describe the case particulars…" className="font-serif text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-ink-muted mb-1.5">Draft text</label>
          <div className="mb-2">
            <DocumentUpload
              label="Upload draft document"
              onExtracted={(text, filename) => setDraftText((prev) => appendExtractedText(prev, text, filename))}
            />
          </div>
          <Textarea
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            required
            rows={14}
            placeholder="Paste the petition/application text to review…"
            className="font-mono text-xs"
          />
        </div>
        {error && <p className="text-sm text-verdict-red">{error}</p>}
        <Button type="submit" disabled={loading || !draftText.trim()}>
          <SearchCheck size={14} />
          {loading ? "Reviewing…" : "Proofread"}
        </Button>
      </form>

      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 rounded-lg border border-border bg-paper-raised p-5">
          <AgentTraceLoader done={false} />
        </motion.div>
      )}

      {report && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-8 space-y-4">
          <div className="rounded-lg border border-verdict-amber/30 bg-verdict-amber-bg px-4 py-3 flex items-start gap-2">
            <AlertTriangle size={15} className="text-verdict-amber shrink-0 mt-0.5" />
            <p className="text-sm text-ink font-serif">{report.summary}</p>
          </div>
          <FindingsList findings={report.findings} />
        </motion.div>
      )}

      <div className="mt-12">
        <p className="text-xs uppercase tracking-wide text-ink-faint mb-3">Recent reports</p>
        {recent === null ? (
          <Skeleton className="h-16 w-full" />
        ) : recent.length === 0 ? (
          <p className="text-sm text-ink-faint">No proofreading reports yet.</p>
        ) : (
          <div className="space-y-2">
            {recent.map((r) => (
              <Card key={r.id}>
                <CardContent className="pt-3 pb-3 flex items-center justify-between gap-3">
                  <p className="text-xs text-ink-muted font-serif line-clamp-1">{r.summary}</p>
                  <p className="text-xs text-ink-faint shrink-0">
                    {r.finding_count} finding{r.finding_count === 1 ? "" : "s"} · {formatDateTime(r.created_at)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

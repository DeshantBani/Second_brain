"use client";

import { useState } from "react";
import { Lock, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogBody, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { StampMark } from "@/components/shared/StampMark";
import { api, ApiError } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import type { ReliabilityOutcomeOut } from "@/lib/types";

export function ReviewGate({
  queryLogId,
  outcome,
  onReviewed,
}: {
  queryLogId: string;
  outcome: ReliabilityOutcomeOut;
  onReviewed: (reviewedAt: string, reviewedBy: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (outcome.reviewed_at) {
    return <StampMark reviewedBy={getStoredUser()?.display_name || "reviewer"} reviewedAt={outcome.reviewed_at} />;
  }

  const confirm = async () => {
    if (!outcome.reliability_assessment_id) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = (await api.reviewAssessment(queryLogId, outcome.reliability_assessment_id)) as {
        reviewed_at: string;
      };
      const user = getStoredUser();
      onReviewed(res.reviewed_at, user?.display_name || "reviewer");
      setOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not record review.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)} disabled={outcome.blocked_by_guardrail}>
        <Lock size={13} />
        Use in drafting
      </Button>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogHeader>
          <DialogTitle>Confirm before use</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <p className="text-sm text-ink-muted mb-4">
            This reliability assessment is a prompt to verify, not a clearance. Review the underlying sources
            below before this language is used in a draft.
          </p>
          <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin rounded border border-border p-3">
            {outcome.sources.map((s, i) => (
              <div key={i} className="text-sm">
                <p className="font-mono text-xs text-accent">{s.citation} — {s.status.replace(/_/g, " ")}</p>
                <p className="font-serif text-ink-muted italic mt-1">&ldquo;{s.treatment_excerpt}&rdquo;</p>
              </div>
            ))}
            {outcome.points_needing_fresh_work.map((p, i) => (
              <div key={i} className="text-sm border-t border-border pt-2">
                <p className="text-ink">{p.point}</p>
              </div>
            ))}
          </div>
          <label className="flex items-start gap-2 mt-4 text-sm text-ink">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              className="mt-0.5"
            />
            I have reviewed the underlying sources and take responsibility for this assessment's use.
          </label>
          {error && <p className="text-xs text-verdict-red mt-2">{error}</p>}
        </DialogBody>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button size="sm" disabled={!checked || submitting} onClick={confirm}>
            <ExternalLink size={13} />
            {submitting ? "Recording…" : "Confirm review"}
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
}

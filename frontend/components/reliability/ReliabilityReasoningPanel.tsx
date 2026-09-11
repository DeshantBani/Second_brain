"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ReliabilityBadge } from "./ReliabilityBadge";
import { ReviewGate } from "./ReviewGate";
import { SourceCitationPill } from "@/components/citations/SourceCitationPill";
import type { QueryTopMatterDocument, ReliabilityOutcomeOut } from "@/lib/types";

export function ReliabilityReasoningPanel({
  queryLogId,
  outcome,
  documents,
}: {
  queryLogId: string;
  outcome: ReliabilityOutcomeOut;
  documents: QueryTopMatterDocument[];
}) {
  const [local, setLocal] = useState(outcome);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-ink-muted mb-1">
            {local.citation}
          </p>
          <p className="text-sm text-ink-muted">{local.court}, {local.year}</p>
        </div>
        <ReliabilityBadge outcome={local} />
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs uppercase tracking-wide text-ink-faint">Relied upon for</p>
        <p className="text-sm text-ink font-serif -mt-3">{local.relied_upon_for}</p>

        {local.blocked_by_guardrail ? (
          <div className="rounded border border-verdict-grey/30 bg-verdict-grey-bg p-3 text-sm text-ink-muted">
            <p className="font-medium text-ink mb-1">This result was withheld, not shown as a verdict.</p>
            <p>The citation-verification guardrail could not confirm every claim against the source data:</p>
            <ul className="list-disc list-inside mt-1">
              {local.guardrail_failure_reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        ) : (
          <>
            <Separator />
            <div>
              <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Reasoning</p>
              <p className="text-sm text-ink font-serif leading-relaxed">{local.reasoning}</p>
            </div>

            {local.points_needing_fresh_work.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-faint mb-2">Needs fresh work</p>
                <ul className="space-y-2">
                  {local.points_needing_fresh_work.map((p, i) => (
                    <li key={i} className="text-sm text-ink flex flex-wrap items-center gap-2">
                      <span>{p.point}</span>
                      <SourceCitationPill documents={documents} sourceRef={p.source_ref} />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {local.sources.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-faint mb-2">Provider-sourced treatment</p>
                <div className="space-y-2">
                  {local.sources.map((s, i) => (
                    <div key={i} className="rounded border border-border p-2.5 text-sm">
                      <p className="font-mono text-xs text-accent">{s.citation} — {s.status.replace(/_/g, " ")}</p>
                      <p className="font-serif text-ink-muted italic mt-1">&ldquo;{s.treatment_excerpt}&rdquo;</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Separator />
            <ReviewGate
              queryLogId={queryLogId}
              outcome={local}
              onReviewed={(reviewedAt) => setLocal({ ...local, reviewed_at: reviewedAt, needs_review: false })}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}

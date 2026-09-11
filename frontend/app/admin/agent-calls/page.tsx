"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AgentCallLogTable } from "@/components/admin/AgentCallLogTable";
import { api, ApiError } from "@/lib/api";
import type { AgentCallLogOut } from "@/lib/types";

function AgentCallsInner() {
  const searchParams = useSearchParams();
  const pipelineRunId = searchParams.get("pipeline_run_id") || undefined;
  const [entries, setEntries] = useState<AgentCallLogOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEntries(null);
    api
      .listAgentCalls(pipelineRunId ? { pipeline_run_id: pipelineRunId } : undefined)
      .then(setEntries)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the agent call log."));
  }, [pipelineRunId]);

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">Agent call log</h1>
      <p className="text-sm text-ink-muted mb-4">
        Every raw request sent to, and response received from, Gemini - structured-output generations and
        embeddings alike. A row marked <span className="font-medium text-ink">replayed</span> was served from a
        prior real response because the live call failed (rate limit, outage, or no key configured) - never a
        fabricated result, always something the model actually said at some point. Click a row for the full
        request/response.
      </p>
      {pipelineRunId && (
        <div className="mb-4">
          <Badge variant="accent" className="font-mono">
            filtered to run {pipelineRunId.slice(0, 8)}
          </Badge>
        </div>
      )}
      {error && <p className="text-sm text-verdict-red mb-4">{error}</p>}
      {entries === null ? <Skeleton className="h-64 w-full" /> : <AgentCallLogTable entries={entries} />}
    </div>
  );
}

export default function AgentCallsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <AgentCallsInner />
    </Suspense>
  );
}

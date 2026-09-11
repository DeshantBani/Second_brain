"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { AgentCallDetailDialog } from "./AgentCallDetailDialog";
import { formatDateTime } from "@/lib/format";
import type { AgentCallLogOut } from "@/lib/types";

export function AgentCallLogTable({ entries }: { entries: AgentCallLogOut[] }) {
  const [selected, setSelected] = useState<AgentCallLogOut | null>(null);

  if (entries.length === 0) {
    return <p className="text-sm text-ink-faint py-8 text-center">No agent calls logged yet - run a query first.</p>;
  }

  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-black/[0.02] text-left text-xs uppercase tracking-wide text-ink-faint">
              <th className="px-4 py-2.5 font-medium">Time</th>
              <th className="px-4 py-2.5 font-medium">Agent</th>
              <th className="px-4 py-2.5 font-medium">Model</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Duration</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr
                key={e.id}
                onClick={() => setSelected(e)}
                className="border-b border-border last:border-0 hover:bg-black/[0.015] cursor-pointer"
              >
                <td className="px-4 py-2.5 text-xs text-ink-faint whitespace-nowrap">{formatDateTime(e.created_at)}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink">{e.agent_name}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink-muted">{e.model}</td>
                <td className="px-4 py-2.5">
                  <div className="flex gap-1">
                    {e.success ? <Badge variant="green">success</Badge> : <Badge variant="red">failed</Badge>}
                    {e.replayed_from_cache && <Badge variant="accent">replayed</Badge>}
                  </div>
                </td>
                <td className="px-4 py-2.5 text-xs text-ink-faint">{e.duration_ms}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <AgentCallDetailDialog entry={selected} open={Boolean(selected)} onClose={() => setSelected(null)} />
    </>
  );
}

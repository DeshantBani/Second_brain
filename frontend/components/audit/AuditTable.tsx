"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { AuditDetailSheet } from "./AuditDetailSheet";
import { formatDateTime } from "@/lib/format";
import type { AuditLogOut } from "@/lib/types";

export function AuditTable({ entries }: { entries: AuditLogOut[] }) {
  const [selected, setSelected] = useState<AuditLogOut | null>(null);

  if (entries.length === 0) {
    return <p className="text-sm text-ink-faint py-8 text-center">No queries logged yet.</p>;
  }

  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-black/[0.02] text-left text-xs uppercase tracking-wide text-ink-faint">
              <th className="px-4 py-2.5 font-medium">Time</th>
              <th className="px-4 py-2.5 font-medium">User</th>
              <th className="px-4 py-2.5 font-medium">Source</th>
              <th className="px-4 py-2.5 font-medium">Query</th>
              <th className="px-4 py-2.5 font-medium">Flags</th>
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
                <td className="px-4 py-2.5 text-xs font-mono text-ink-muted">{e.user_email}</td>
                <td className="px-4 py-2.5">
                  <Badge variant="outline">{e.source}</Badge>
                </td>
                <td className="px-4 py-2.5 text-ink max-w-xs truncate">{e.query_text}</td>
                <td className="px-4 py-2.5">
                  <div className="flex gap-1">
                    {e.no_confident_match && <Badge variant="grey">no match</Badge>}
                    {e.degraded_mode && <Badge variant="amber">degraded</Badge>}
                    {e.blocked_by_guardrail && <Badge variant="red">blocked</Badge>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <AuditDetailSheet entry={selected} open={Boolean(selected)} onClose={() => setSelected(null)} />
    </>
  );
}

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Dialog, DialogBody, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/format";
import type { AuditLogOut } from "@/lib/types";

export function AuditDetailSheet({
  entry,
  open,
  onClose,
}: {
  entry: AuditLogOut | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!entry) return null;
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogHeader>
        <DialogTitle>Query audit entry</DialogTitle>
      </DialogHeader>
      <DialogBody className="space-y-3 text-sm">
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline">{entry.source}</Badge>
          {entry.no_confident_match && <Badge variant="grey">no confident match</Badge>}
          {entry.degraded_mode && <Badge variant="amber">degraded mode</Badge>}
          {entry.replayed_from_cache && <Badge variant="accent">replayed from cache</Badge>}
          {entry.blocked_by_guardrail && <Badge variant="red">guardrail blocked</Badge>}
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">User</p>
          <p className="text-ink font-mono text-xs">{entry.user_email}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Query</p>
          <p className="text-ink font-serif">{entry.query_text}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Time</p>
          <p className="text-ink">{formatDateTime(entry.created_at)}</p>
        </div>
        {entry.pipeline_run_id && (
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Pipeline run</p>
            <Link
              href={`/admin/agent-calls?pipeline_run_id=${entry.pipeline_run_id}`}
              className="inline-flex items-center gap-1 text-xs font-mono text-accent hover:underline"
            >
              {entry.pipeline_run_id} <ArrowUpRight size={11} />
            </Link>
          </div>
        )}
      </DialogBody>
    </Dialog>
  );
}

import { Dialog, DialogBody, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatDateTime } from "@/lib/format";
import type { AgentCallLogOut } from "@/lib/types";

function prettyPrint(text: string | null): string {
  if (!text) return "";
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

export function AgentCallDetailDialog({
  entry,
  open,
  onClose,
}: {
  entry: AgentCallLogOut | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!entry) return null;
  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader>
        <DialogTitle className="font-mono text-base">{entry.agent_name}</DialogTitle>
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          <Badge variant="outline" className="font-mono">{entry.model}</Badge>
          {entry.success ? <Badge variant="green">success</Badge> : <Badge variant="red">failed</Badge>}
          {entry.replayed_from_cache && <Badge variant="accent">replayed from cache</Badge>}
          <Badge variant="outline">{entry.duration_ms}ms</Badge>
        </div>
        <p className="text-xs text-ink-faint mt-1.5">
          {formatDateTime(entry.created_at)}
          {entry.pipeline_run_id && <> · run <span className="font-mono">{entry.pipeline_run_id.slice(0, 8)}</span></>}
        </p>
      </DialogHeader>
      <DialogBody className="max-h-[65vh] overflow-y-auto scrollbar-thin space-y-4">
        {entry.error_message && (
          <div className="rounded border border-verdict-red/30 bg-verdict-red-bg p-3">
            <p className="text-xs uppercase tracking-wide text-verdict-red mb-1">Error</p>
            <p className="text-sm text-ink font-mono whitespace-pre-wrap break-words">{entry.error_message}</p>
          </div>
        )}
        {entry.system_instruction && (
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">System instruction</p>
            <pre className="text-xs text-ink-muted bg-black/[0.02] rounded p-3 whitespace-pre-wrap break-words font-mono max-h-40 overflow-y-auto scrollbar-thin">
              {entry.system_instruction}
            </pre>
          </div>
        )}
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Input (user content)</p>
          <pre className="text-xs text-ink bg-black/[0.02] rounded p-3 whitespace-pre-wrap break-words font-mono max-h-56 overflow-y-auto scrollbar-thin">
            {entry.user_content}
          </pre>
        </div>
        <Separator />
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Raw response</p>
          <pre className="text-xs text-ink bg-accent-soft rounded p-3 whitespace-pre-wrap break-words font-mono max-h-72 overflow-y-auto scrollbar-thin">
            {prettyPrint(entry.raw_response_text) || "—"}
          </pre>
        </div>
        <p className="text-[11px] text-ink-faint font-mono break-all">cache_key: {entry.cache_key}</p>
      </DialogBody>
    </Dialog>
  );
}

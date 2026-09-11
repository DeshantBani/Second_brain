import Link from "next/link";
import { ArrowUpRight, FileEdit } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/format";
import type { DraftingSessionSummary } from "@/lib/types";

const STATUS_VARIANT: Record<string, "grey" | "amber" | "green"> = {
  gathering: "grey",
  ready: "amber",
  drafted: "green",
};

const STATUS_LABEL: Record<string, string> = {
  gathering: "gathering requirements",
  ready: "ready to draft",
  drafted: "drafted",
};

export function DraftSessionList({ sessions }: { sessions: DraftingSessionSummary[] }) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center text-center py-16">
        <FileEdit size={20} className="text-ink-faint mb-3" />
        <p className="text-sm text-ink-faint">No drafting sessions yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {sessions.map((s) => (
        <Link key={s.id} href={`/draft/${s.id}`}>
          <Card className="hover:border-ink/30 transition-colors">
            <CardContent className="pt-4 pb-4 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm text-ink font-serif line-clamp-2">{s.case_brief}</p>
                <p className="text-xs text-ink-faint mt-1.5">{formatDateTime(s.updated_at)}</p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <Badge variant={STATUS_VARIANT[s.status]}>{STATUS_LABEL[s.status]}</Badge>
                <ArrowUpRight size={14} className="text-ink-faint" />
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

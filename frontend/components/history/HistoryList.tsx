import Link from "next/link";
import { ArrowUpRight, History as HistoryIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/format";
import type { QueryHistoryItem } from "@/lib/types";

export function HistoryList({ items }: { items: QueryHistoryItem[] }) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center text-center py-16">
        <HistoryIcon size={20} className="text-ink-faint mb-3" />
        <p className="text-sm text-ink-faint">No queries yet - run one from the home page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {items.map((item) => (
        <Link key={item.query_log_id} href={`/query/${item.query_log_id}`}>
          <Card className="hover:border-ink/30 transition-colors">
            <CardContent className="pt-4 pb-4 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm text-ink font-serif line-clamp-2">{item.query_text}</p>
                <p className="text-xs text-ink-faint mt-1.5">
                  {formatDateTime(item.created_at)} · <span className="font-mono">{item.source}</span>
                </p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {item.no_confident_match && <Badge variant="grey">no match</Badge>}
                {item.degraded_mode && <Badge variant="amber">degraded</Badge>}
                {item.replayed_from_cache && <Badge variant="accent">replayed</Badge>}
                {item.blocked_by_guardrail && <Badge variant="red">blocked</Badge>}
                <ArrowUpRight size={14} className="text-ink-faint" />
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

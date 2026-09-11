import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/format";
import type { MatterSummary } from "@/lib/types";

export function MatterList({ matters }: { matters: MatterSummary[] }) {
  if (matters.length === 0) {
    return <p className="text-sm text-ink-faint py-8 text-center">No matters accessible to your account.</p>;
  }
  return (
    <div className="space-y-3">
      {matters.map((m) => (
        <Link key={m.id} href={`/matters/${m.id}`}>
          <Card className="hover:border-ink/30 transition-colors">
            <CardContent className="pt-5 flex items-start justify-between gap-4">
              <div>
                <p className="font-display text-[16px] text-ink mb-1">{m.title}</p>
                <p className="text-xs text-ink-faint">
                  {m.client_name} · {m.practice_area.replace(/_/g, " ")} · {m.jurisdiction} · opened{" "}
                  {formatDate(m.opened_date)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={m.status === "open" ? "amber" : "outline"}>{m.status}</Badge>
                <ArrowUpRight size={14} className="text-ink-faint" />
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

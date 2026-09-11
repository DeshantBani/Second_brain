import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { RankedMatterOut } from "@/lib/types";

const CONFIDENCE_VARIANT: Record<string, "green" | "amber" | "grey"> = {
  high: "green",
  medium: "amber",
  low: "grey",
};

export function RankedMatterCard({ matter, top }: { matter: RankedMatterOut; top?: boolean }) {
  return (
    <Card className={cn(top && "border-ink/25 shadow-raised")}>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-black/[0.05] text-xs font-mono text-ink-muted">
              {matter.rank}
            </span>
            <p className="font-display text-[17px] text-ink leading-snug">{matter.title}</p>
          </div>
          <Badge variant={CONFIDENCE_VARIANT[matter.confidence]}>{matter.confidence} confidence</Badge>
        </div>
        <p className="text-xs text-ink-faint mb-2">
          {matter.client_name} · {matter.practice_area.replace(/_/g, " ")} · {matter.jurisdiction}
        </p>
        <p className="text-sm text-ink-muted font-serif leading-relaxed mb-3">{matter.similarity_rationale}</p>
        <Link
          href={`/matters/${matter.matter_id}`}
          className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
        >
          View matter file <ArrowUpRight size={12} />
        </Link>
      </CardContent>
    </Card>
  );
}

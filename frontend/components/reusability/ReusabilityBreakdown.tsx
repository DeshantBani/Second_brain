import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { SourceCitationPill } from "@/components/citations/SourceCitationPill";
import { titleCase } from "@/lib/format";
import type { ReusabilityBreakdown as ReusabilityBreakdownType, QueryTopMatterDocument } from "@/lib/types";

const REUSABILITY_VARIANT: Record<string, "green" | "amber" | "red"> = {
  fully_reusable: "green",
  adapt_required: "amber",
  not_reusable: "red",
};

export function ReusabilityBreakdownView({
  breakdown,
  documents,
}: {
  breakdown: ReusabilityBreakdownType;
  documents: QueryTopMatterDocument[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {breakdown.components.map((c, i) => (
        <Card key={i}>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between mb-2">
              <p className="font-display text-[15px] text-ink">{titleCase(c.component)}</p>
              <Badge variant={REUSABILITY_VARIANT[c.reusability]}>{titleCase(c.reusability)}</Badge>
            </div>
            <p className="text-sm text-ink-muted font-serif leading-relaxed mb-2">{c.notes}</p>
            <SourceCitationPill documents={documents} sourceRef={c.source_ref} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

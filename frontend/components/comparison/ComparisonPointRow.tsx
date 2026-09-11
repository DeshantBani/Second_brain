import { Badge } from "@/components/ui/badge";
import { SourceCitationPill } from "@/components/citations/SourceCitationPill";
import type { ComparisonPoint, DifferencePoint, QueryTopMatterDocument } from "@/lib/types";

export function ComparisonPointRow({
  point,
  documents,
}: {
  point: ComparisonPoint | DifferencePoint;
  documents: QueryTopMatterDocument[];
}) {
  const materiality = (point as DifferencePoint).materiality;
  return (
    <div className="py-2.5 flex flex-wrap items-start gap-x-2 gap-y-1.5">
      {materiality && (
        <Badge variant={materiality === "material" ? "amber" : "outline"} className="mt-0.5 shrink-0">
          {materiality}
        </Badge>
      )}
      <p className="text-sm text-ink font-serif leading-relaxed flex-1 min-w-[200px]">{point.point}</p>
      <SourceCitationPill documents={documents} sourceRef={point.source_ref} />
    </div>
  );
}

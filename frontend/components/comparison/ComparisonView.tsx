import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ComparisonPointRow } from "./ComparisonPointRow";
import type { ComparisonResult, QueryTopMatterDocument } from "@/lib/types";
import { AlertTriangle } from "lucide-react";

export function ComparisonView({
  comparison,
  documents,
}: {
  comparison: ComparisonResult;
  documents: QueryTopMatterDocument[];
}) {
  return (
    <div className="space-y-6">
      <p className="font-serif text-[15px] text-ink-muted leading-relaxed">{comparison.summary}</p>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Similarities</CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-border">
            {comparison.similarities.length === 0 && (
              <p className="text-sm text-ink-faint">No notable similarities identified.</p>
            )}
            {comparison.similarities.map((p, i) => (
              <ComparisonPointRow key={i} point={p} documents={documents} />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Material differences</CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-border">
            {comparison.differences.length === 0 && (
              <p className="text-sm text-ink-faint">No differences identified.</p>
            )}
            {comparison.differences.map((p, i) => (
              <ComparisonPointRow key={i} point={p} documents={documents} />
            ))}
          </CardContent>
        </Card>
      </div>

      {comparison.flags.length > 0 && (
        <div className="rounded-lg border border-verdict-amber/30 bg-verdict-amber-bg p-4">
          <p className="flex items-center gap-1.5 text-sm font-medium text-verdict-amber mb-1.5">
            <AlertTriangle size={14} />
            Flags
          </p>
          <ul className="list-disc list-inside space-y-1">
            {comparison.flags.map((f, i) => (
              <li key={i} className="text-sm text-ink font-serif">{f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

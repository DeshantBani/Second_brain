import { AlertTriangle, FileWarning, SearchX } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ProofreadingFindingOut } from "@/lib/types";

const CATEGORY_META: Record<string, { label: string; icon: typeof AlertTriangle }> = {
  format: { label: "Format", icon: FileWarning },
  content: { label: "Content", icon: AlertTriangle },
  missing_fact: { label: "Missing fact", icon: SearchX },
};

const SEVERITY_VARIANT: Record<string, "red" | "amber" | "grey"> = {
  high: "red",
  medium: "amber",
  low: "grey",
};

export function FindingsList({ findings }: { findings: ProofreadingFindingOut[] }) {
  if (findings.length === 0) {
    return (
      <p className="text-sm text-ink-muted font-serif">
        No specific findings were raised — that is not the same as a clean bill of health; review the draft
        yourself before relying on this.
      </p>
    );
  }

  return (
    <div className="space-y-2.5">
      {findings.map((f, i) => {
        const meta = CATEGORY_META[f.category];
        const Icon = meta.icon;
        return (
          <Card key={i}>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start justify-between gap-3 mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Icon size={13} className="text-ink-faint" />
                  <Badge variant="outline">{meta.label}</Badge>
                  <span className="text-xs text-ink-faint">· {f.section}</span>
                </div>
                <Badge variant={SEVERITY_VARIANT[f.severity]}>{f.severity}</Badge>
              </div>
              <p className="text-sm text-ink font-serif mb-1.5">{f.issue}</p>
              <p className="text-sm text-ink-muted">
                <span className="font-medium text-ink">Suggestion: </span>
                {f.suggestion}
              </p>
              {f.grounding_excerpt && (
                <p className="text-xs text-accent font-serif italic mt-2 border-l-2 border-accent/30 pl-2.5">
                  &ldquo;{f.grounding_excerpt}&rdquo;
                </p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

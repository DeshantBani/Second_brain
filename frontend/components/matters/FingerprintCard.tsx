import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { FingerprintOut } from "@/lib/types";

export function FingerprintCard({ fingerprint }: { fingerprint: FingerprintOut }) {
  const clauses = (fingerprint.contract_clauses?.clauses as Array<{ clause_type: string; exists: boolean; key_terms: string }>) || [];
  const factualPattern = (fingerprint.factual_pattern?.text as string) || "";

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-5 grid gap-4 sm:grid-cols-3 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Jurisdiction</p>
            <p className="text-ink">{fingerprint.jurisdiction}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Practice area</p>
            <p className="text-ink">{fingerprint.practice_area.replace(/_/g, " ")}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-1">Procedural posture</p>
            <p className="text-ink">{fingerprint.procedural_posture}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5">
          <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Summary</p>
          <p className="text-sm text-ink font-serif leading-relaxed mb-4">{fingerprint.summary}</p>
          {factualPattern && (
            <>
              <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Factual pattern</p>
              <p className="text-sm text-ink-muted font-serif leading-relaxed">{factualPattern}</p>
            </>
          )}
        </CardContent>
      </Card>

      {clauses.length > 0 && (
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-2">Contract clauses</p>
            <div className="space-y-2">
              {clauses.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <Badge variant={c.exists ? "accent" : "outline"}>{c.exists ? "present" : "absent"}</Badge>
                  <span className="text-ink font-medium">{c.clause_type.replace(/_/g, " ")}</span>
                  {c.key_terms && <span className="text-ink-muted">— {c.key_terms}</span>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap gap-1.5">
        {fingerprint.clause_tags.map((tag) => (
          <Badge key={tag} variant="outline" className="font-mono">
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  );
}

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { GatheredRequirements } from "@/lib/types";

export function GatheredRequirementsCard({ requirements }: { requirements: GatheredRequirements }) {
  return (
    <Card>
      <CardContent className="pt-5 space-y-3 text-sm">
        <p className="text-xs uppercase tracking-wide text-ink-faint">Confirmed before drafting</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs text-ink-faint mb-0.5">Petition type</p>
            <p className="text-ink">{requirements.petition_type}</p>
          </div>
          <div>
            <p className="text-xs text-ink-faint mb-0.5">Forum</p>
            <p className="text-ink">{requirements.forum}</p>
          </div>
          <div>
            <p className="text-xs text-ink-faint mb-0.5">Petitioner</p>
            <p className="text-ink">{requirements.petitioner}</p>
          </div>
          <div>
            <p className="text-xs text-ink-faint mb-0.5">Respondent</p>
            <p className="text-ink">{requirements.respondent}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-ink-faint mb-1">Grounds</p>
          <ul className="list-disc list-inside space-y-0.5">
            {requirements.grounds.map((g, i) => (
              <li key={i} className="text-ink font-serif">{g}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs text-ink-faint mb-0.5">Relief sought</p>
          <p className="text-ink font-serif">{requirements.relief_sought}</p>
        </div>
      </CardContent>
    </Card>
  );
}

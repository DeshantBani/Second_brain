import { ShieldAlert, ShieldCheck, ShieldQuestion, ShieldX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ReliabilityOutcomeOut } from "@/lib/types";

/** Four explicit, deliberately worded states - never "cleared" or "safe". A verdict is
 * always a prompt to verify; the badge's job is to make "checked vs. not checked"
 * impossible to miss, per the non-negotiable in the build plan. */
export function ReliabilityBadge({ outcome }: { outcome: ReliabilityOutcomeOut }) {
  if (outcome.blocked_by_guardrail) {
    return (
      <Badge variant="grey">
        <ShieldX size={12} />
        Verification failed — withheld
      </Badge>
    );
  }

  if (!outcome.verdict) {
    return (
      <Badge variant="grey">
        <ShieldQuestion size={12} />
        Not checked
      </Badge>
    );
  }

  if (outcome.verdict === "green") {
    return (
      <Badge variant="green">
        <ShieldCheck size={12} />
        No adverse treatment found — verify before relying
      </Badge>
    );
  }

  if (outcome.verdict === "amber") {
    return (
      <Badge variant="amber">
        <ShieldAlert size={12} />
        Verify before relying — points flagged
      </Badge>
    );
  }

  return (
    <Badge variant="red">
      <ShieldAlert size={12} />
      Do not rely without fresh review
    </Badge>
  );
}

import { Lock, Users, Globe } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const TIER_META: Record<string, { label: string; icon: typeof Lock; variant: "default" | "outline" }> = {
  tier1_confidential: { label: "Confidential", icon: Lock, variant: "default" },
  tier2_internal: { label: "Internal", icon: Users, variant: "outline" },
  tier3_publishable: { label: "Publishable", icon: Globe, variant: "outline" },
};

export function ConfidentialityTierPill({ tier }: { tier: string }) {
  const meta = TIER_META[tier] || TIER_META.tier1_confidential;
  const Icon = meta.icon;
  return (
    <Badge variant={meta.variant}>
      <Icon size={11} />
      {meta.label}
    </Badge>
  );
}

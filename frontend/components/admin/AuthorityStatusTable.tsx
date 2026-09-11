"use client";

import { useState } from "react";
import { RefreshCw, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { AuthorityOut } from "@/lib/types";

const STATUS_ICON: Record<string, typeof ShieldCheck> = {
  good_law: ShieldCheck,
  doubted: ShieldAlert,
  distinguished: ShieldAlert,
  overruled: ShieldAlert,
};

const STATUS_VARIANT: Record<string, "green" | "amber" | "red"> = {
  good_law: "green",
  doubted: "amber",
  distinguished: "amber",
  overruled: "red",
};

const MONITORING_VARIANT: Record<string, "grey" | "green" | "amber"> = {
  not_checked: "grey",
  checked_clear: "green",
  checked_flagged: "amber",
};

export function AuthorityStatusTable({ authorities }: { authorities: AuthorityOut[] }) {
  const [rows, setRows] = useState(authorities);
  const [rechecking, setRechecking] = useState<string | null>(null);

  const recheck = async (id: string) => {
    setRechecking(id);
    try {
      const res = (await api.recheckAuthority(id)) as { authority: AuthorityOut };
      setRows((prev) => prev.map((r) => (r.id === id ? res.authority : r)));
    } finally {
      setRechecking(null);
    }
  };

  return (
    <div className="space-y-2">
      {rows.map((a) => {
        const Icon = STATUS_ICON[a.status] || ShieldQuestion;
        return (
          <div key={a.id} className="rounded-lg border border-border bg-paper-raised p-4 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="font-mono text-xs text-ink truncate">{a.citation}</p>
              <p className="text-xs text-ink-faint mt-1">
                {a.court}, {a.year} · last checked {formatDateTime(a.last_checked_at)}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={MONITORING_VARIANT[a.monitoring_status] || "grey"}>
                {a.monitoring_status.replace(/_/g, " ")}
              </Badge>
              <Badge variant={STATUS_VARIANT[a.status] || "grey"}>
                <Icon size={11} />
                {a.status.replace(/_/g, " ")}
              </Badge>
              <Button variant="outline" size="sm" onClick={() => recheck(a.id)} disabled={rechecking === a.id}>
                <RefreshCw size={12} className={rechecking === a.id ? "animate-spin" : ""} />
                Recheck
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

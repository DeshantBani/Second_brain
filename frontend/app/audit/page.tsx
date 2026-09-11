"use client";

import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { AuditTable } from "@/components/audit/AuditTable";
import { api, ApiError } from "@/lib/api";
import type { AuditLogOut } from "@/lib/types";

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditLogOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAudit()
      .then(setEntries)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the audit log."));
  }, []);

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">Audit log</h1>
      <p className="text-sm text-ink-muted mb-6">
        Every query, from every surface, with its source and any flags — the record required to audit the
        reliability layer after the fact.
      </p>
      {error && <p className="text-sm text-verdict-red mb-4">{error}</p>}
      {entries === null ? <Skeleton className="h-64 w-full" /> : <AuditTable entries={entries} />}
    </div>
  );
}

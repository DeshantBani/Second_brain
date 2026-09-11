"use client";

import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { AuthorityStatusTable } from "@/components/admin/AuthorityStatusTable";
import { api, ApiError } from "@/lib/api";
import type { AuthorityOut } from "@/lib/types";

export default function AdminAuthoritiesPage() {
  const [authorities, setAuthorities] = useState<AuthorityOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAuthorities()
      .then(setAuthorities)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load authorities."));
  }, []);

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">Authority monitoring</h1>
      <p className="text-sm text-ink-muted mb-6">
        Every authority tracked by the reliability engine, sourced from the active CaseLawProvider. A background
        job rechecks these hourly — use Recheck to trigger one manually.
      </p>
      {error && <p className="text-sm text-verdict-red mb-4">{error}</p>}
      {authorities === null ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <AuthorityStatusTable authorities={authorities} />
      )}
    </div>
  );
}

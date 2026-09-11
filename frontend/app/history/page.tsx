"use client";

import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { HistoryList } from "@/components/history/HistoryList";
import { api, ApiError } from "@/lib/api";
import type { QueryHistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const [items, setItems] = useState<QueryHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listQueryHistory()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load your query history."));
  }, []);

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">History</h1>
      <p className="text-sm text-ink-muted mb-6">
        Every query you&apos;ve run, most recent first — click one to reopen its full result exactly as it was.
      </p>
      {error && <p className="text-sm text-verdict-red mb-4">{error}</p>}
      {items === null ? (
        <div className="space-y-2.5">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : (
        <HistoryList items={items} />
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { MatterList } from "@/components/matters/MatterList";
import { api } from "@/lib/api";
import type { MatterSummary } from "@/lib/types";

export default function MattersPage() {
  const [matters, setMatters] = useState<MatterSummary[] | null>(null);

  useEffect(() => {
    api.listMatters().then(setMatters).catch(() => setMatters([]));
  }, []);

  return (
    <div>
      <h1 className="font-display text-2xl text-ink mb-1">Matters</h1>
      <p className="text-sm text-ink-muted mb-6">
        Every matter your account has an access grant for — access is enforced at the database layer.
      </p>
      {matters === null ? (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : (
        <MatterList matters={matters} />
      )}
    </div>
  );
}

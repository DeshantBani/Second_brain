"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
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
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-2xl text-ink mb-1">Matters</h1>
          <p className="text-sm text-ink-muted">
            Every matter your account has an access grant for — access is enforced at the database layer.
          </p>
        </div>
        <Link href="/matters/new" className="shrink-0">
          <Button size="sm">
            <Plus size={14} />
            New matter
          </Button>
        </Link>
      </div>
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

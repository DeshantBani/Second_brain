"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MatterDetailTabs } from "@/components/matters/MatterDetailTabs";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { MatterDetail } from "@/lib/types";

export default function MatterDetailPage() {
  const params = useParams<{ id: string }>();
  const [matter, setMatter] = useState<MatterDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = () => {
    api
      .getMatter(params.id)
      .then(setMatter)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this matter."));
  };

  useEffect(refetch, [params.id]);

  if (error) {
    return <p className="text-sm text-verdict-red text-center py-16">{error}</p>;
  }

  if (!matter) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <Badge variant={matter.status === "open" ? "amber" : "outline"}>{matter.status}</Badge>
          <span className="text-xs text-ink-faint">opened {formatDate(matter.opened_date)}</span>
        </div>
        <h1 className="font-display text-2xl text-ink mb-1">{matter.title}</h1>
        <p className="text-sm text-ink-muted">
          {matter.client_name} · {matter.practice_area.replace(/_/g, " ")} · {matter.jurisdiction}
        </p>
      </div>

      <MatterDetailTabs matter={matter} onChanged={refetch} />
    </div>
  );
}

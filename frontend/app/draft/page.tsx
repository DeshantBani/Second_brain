"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DraftSessionList } from "@/components/draft/DraftSessionList";
import { api } from "@/lib/api";
import type { DraftingSessionSummary } from "@/lib/types";

export default function DraftPage() {
  const [sessions, setSessions] = useState<DraftingSessionSummary[] | null>(null);

  useEffect(() => {
    api.listDraftingSessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-2xl text-ink mb-1">Draft</h1>
          <p className="text-sm text-ink-muted">
            Describe your case, answer a few follow-up questions, and get a petition drafted to that exact
            structure and scope - nothing more, nothing less.
          </p>
        </div>
        <Link href="/draft/new" className="shrink-0">
          <Button size="sm">
            <Plus size={14} />
            New draft
          </Button>
        </Link>
      </div>
      {sessions === null ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : (
        <DraftSessionList sessions={sessions} />
      )}
    </div>
  );
}

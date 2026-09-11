"use client";

import { useState } from "react";
import { Quote } from "lucide-react";
import { HoverCard } from "@/components/ui/hover-card";
import { DocumentViewer } from "./DocumentViewer";
import { resolveSourceRef } from "@/lib/sourceRef";
import type { QueryTopMatterDocument, SourceRef } from "@/lib/types";

export function SourceCitationPill({
  documents,
  sourceRef,
}: {
  documents: QueryTopMatterDocument[];
  sourceRef: SourceRef;
}) {
  const [open, setOpen] = useState(false);
  const resolved = resolveSourceRef(documents, sourceRef);
  const doc = documents.find((d) => d.id === sourceRef.document_id) || null;

  return (
    <>
      <HoverCard
        trigger={
          <button
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-1 rounded border border-border bg-accent-soft px-1.5 py-0.5 font-mono text-[11px] text-accent hover:border-accent/40 transition-colors align-middle"
          >
            <Quote size={10} />
            {resolved.documentTitle.length > 24 ? resolved.documentTitle.slice(0, 24) + "…" : resolved.documentTitle} · p.{resolved.page} ¶{resolved.paragraph}
          </button>
        }
      >
        <p className="text-[10px] uppercase tracking-wide text-ink-faint mb-1.5">
          {resolved.documentTitle} — page {resolved.page}, paragraph {resolved.paragraph}
        </p>
        <p className="font-serif text-sm text-ink leading-snug italic">&ldquo;{resolved.text}&rdquo;</p>
        <p className="text-[11px] text-accent mt-2">Click to view in document →</p>
      </HoverCard>
      <DocumentViewer
        open={open}
        onClose={() => setOpen(false)}
        document={doc}
        highlight={{ page: sourceRef.page, paragraph: sourceRef.paragraph }}
      />
    </>
  );
}

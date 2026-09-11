"use client";

import { useEffect, useRef } from "react";
import { Dialog, DialogBody, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import type { QueryTopMatterDocument } from "@/lib/types";

export function DocumentViewer({
  open,
  onClose,
  document,
  highlight,
}: {
  open: boolean;
  onClose: () => void;
  document: QueryTopMatterDocument | null;
  highlight?: { page: number; paragraph: number };
}) {
  const highlightRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open && highlightRef.current) {
      const t = setTimeout(() => {
        highlightRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
      }, 150);
      return () => clearTimeout(t);
    }
  }, [open, highlight]);

  if (!document) return null;

  let currentPage: number | null = null;

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>{document.title}</DialogTitle>
        <p className="text-xs text-ink-faint mt-1 uppercase tracking-wide">{document.doc_type.replace(/_/g, " ")}</p>
      </DialogHeader>
      <DialogBody className="max-h-[60vh] overflow-y-auto scrollbar-thin">
        <div className="font-serif text-[15px] leading-relaxed text-ink space-y-4">
          {document.page_map.map((entry) => {
            const isHighlighted = highlight && entry.page === highlight.page && entry.paragraph === highlight.paragraph;
            const showPageMarker = entry.page !== currentPage;
            currentPage = entry.page;
            return (
              <div key={`${entry.page}-${entry.paragraph}`}>
                {showPageMarker && (
                  <div className="flex items-center gap-2 my-3 first:mt-0">
                    <Badge variant="outline" className="font-mono">
                      Page {entry.page}
                    </Badge>
                    <div className="h-px flex-1 bg-border" />
                  </div>
                )}
                <div
                  ref={isHighlighted ? highlightRef : undefined}
                  className={
                    isHighlighted
                      ? "rounded bg-verdict-amber-bg border border-verdict-amber/30 px-3 py-2 -mx-3"
                      : ""
                  }
                >
                  <span className="text-ink-faint text-xs font-mono mr-2 select-none">¶{entry.paragraph}</span>
                  {entry.text}
                </div>
              </div>
            );
          })}
        </div>
      </DialogBody>
    </Dialog>
  );
}

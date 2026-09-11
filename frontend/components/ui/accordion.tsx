"use client";

import { ReactNode, useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/cn";

export function AccordionItem({
  title,
  defaultOpen = false,
  children,
  className,
  badge,
}: {
  title: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
  badge?: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={cn("border border-border rounded-lg overflow-hidden bg-paper-raised", className)}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-black/[0.02] transition-colors"
      >
        <span className="flex items-center gap-2 min-w-0">
          <span className="font-medium text-sm text-ink truncate">{title}</span>
          {badge}
        </span>
        <ChevronDown
          size={16}
          className={cn("shrink-0 text-ink-muted transition-transform duration-200", open && "rotate-180")}
        />
      </button>
      {open && <div className="px-4 pb-4 pt-1 border-t border-border">{children}</div>}
    </div>
  );
}

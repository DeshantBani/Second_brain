"use client";

import { ReactNode, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";

export function HoverCard({
  trigger,
  children,
  className,
}: {
  trigger: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (timeout.current) clearTimeout(timeout.current);
    setOpen(true);
  };
  const hide = () => {
    timeout.current = setTimeout(() => setOpen(false), 120);
  };

  return (
    <span className="relative inline-block" onMouseEnter={show} onMouseLeave={hide}>
      {trigger}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "absolute left-1/2 top-full z-40 mt-2 w-80 -translate-x-1/2 rounded-lg border border-border bg-paper-raised p-4 shadow-raised",
              className
            )}
            onMouseEnter={show}
            onMouseLeave={hide}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}

"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";

const STEPS = [
  "Extracting issue fingerprint",
  "Filtering and ranking the archive",
  "Comparing against the closest matter",
  "Checking reliability of relied-upon authorities",
];

export function AgentTraceLoader({ done }: { done: boolean }) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (done) {
      setActiveIndex(STEPS.length);
      return;
    }
    if (activeIndex >= STEPS.length - 1) return;
    const t = setTimeout(() => setActiveIndex((i) => i + 1), 1100);
    return () => clearTimeout(t);
  }, [activeIndex, done]);

  return (
    <div className="space-y-3">
      {STEPS.map((step, i) => {
        const complete = i < activeIndex || done;
        const active = i === activeIndex && !done;
        return (
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: i <= activeIndex || done ? 1 : 0.3, x: 0 }}
            transition={{ duration: 0.25 }}
            className="flex items-center gap-3"
          >
            <span
              className={
                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] " +
                (complete
                  ? "border-verdict-green bg-verdict-green-bg text-verdict-green"
                  : active
                  ? "border-accent text-accent"
                  : "border-border text-ink-faint")
              }
            >
              {complete ? <Check size={12} /> : active ? <Loader2 size={12} className="animate-spin" /> : i + 1}
            </span>
            <span className={"text-sm " + (complete ? "text-ink" : active ? "text-ink" : "text-ink-faint")}>
              {step}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}

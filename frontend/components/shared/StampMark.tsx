"use client";

import { motion } from "framer-motion";
import { formatDateTime } from "@/lib/format";

export function StampMark({ reviewedBy, reviewedAt }: { reviewedBy: string; reviewedAt: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 1.4, rotate: -8 }}
      animate={{ opacity: 1, scale: 1, rotate: -6 }}
      transition={{ type: "spring", stiffness: 260, damping: 16 }}
      className="inline-flex flex-col items-center rounded border-2 border-verdict-green px-3 py-1.5 text-verdict-green select-none"
      style={{ transform: "rotate(-6deg)" }}
    >
      <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.15em]">Reviewed</span>
      <span className="font-mono text-[9px] uppercase tracking-wide">{reviewedBy}</span>
      <span className="font-mono text-[9px] text-verdict-green/80">{formatDateTime(reviewedAt)}</span>
    </motion.div>
  );
}

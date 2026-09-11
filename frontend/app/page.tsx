"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { QueryBox } from "@/components/query/QueryBox";
import { ExamplePrompts } from "@/components/query/ExamplePrompts";
import { AgentTraceLoader } from "@/components/query/AgentTraceLoader";
import { api, ApiError } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.submitQuery(text, "web");
      try {
        sessionStorage.setItem(`query_result_${result.query_log_id}`, JSON.stringify(result));
      } catch {
        // sessionStorage unavailable - the query page will just re-fetch via GET
      }
      router.push(`/query/${result.query_log_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the reasoning engine.");
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center py-16 sm:py-24">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-2xl text-center"
      >
        <h1 className="font-display text-3xl sm:text-4xl text-ink tracking-tight mb-3">
          Have we advised on this before?
        </h1>
        <p className="text-ink-muted text-[15px] mb-10 max-w-lg mx-auto">
          Describe the problem the way you would to a colleague. The archive is matched by legal
          issue, not keywords — every result is graded, compared, and sourced.
        </p>

        <QueryBox value={text} onChange={setText} onSubmit={submit} loading={loading} />

        {!loading && (
          <div className="mt-5">
            <ExamplePrompts onSelect={setText} />
          </div>
        )}

        {error && <p className="mt-4 text-sm text-verdict-red">{error}</p>}

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-10 rounded-lg border border-border bg-paper-raised p-6 text-left"
          >
            <AgentTraceLoader done={false} />
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { RankedMatterCard } from "@/components/results/RankedMatterCard";
import { NoConfidentMatch } from "@/components/results/NoConfidentMatch";
import { ComparisonView } from "@/components/comparison/ComparisonView";
import { ReusabilityBreakdownView } from "@/components/reusability/ReusabilityBreakdown";
import { ReliabilityReasoningPanel } from "@/components/reliability/ReliabilityReasoningPanel";
import { api, ApiError } from "@/lib/api";
import type { QueryResultOut } from "@/lib/types";
import { AlertTriangle } from "lucide-react";

export default function QueryResultPage() {
  const params = useParams<{ id: string }>();
  const [result, setResult] = useState<QueryResultOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cached: QueryResultOut | null = null;
    try {
      const raw = sessionStorage.getItem(`query_result_${params.id}`);
      if (raw) cached = JSON.parse(raw);
    } catch {
      // ignore
    }
    if (cached) {
      setResult(cached);
      return;
    }
    api
      .getQuery(params.id)
      .then(setResult)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this query."));
  }, [params.id]);

  if (error) {
    return <p className="text-sm text-verdict-red text-center py-16">{error}</p>;
  }

  if (!result) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  const documents = result.top_matter?.documents || [];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Query</p>
        <p className="font-serif text-lg text-ink leading-snug">{result.query_text}</p>
        <div className="flex items-center gap-2 mt-3">
          {result.degraded_mode && (
            <Badge variant="amber">
              <AlertTriangle size={11} />
              Degraded mode
            </Badge>
          )}
        </div>
      </div>

      {result.no_confident_match ? (
        <NoConfidentMatch rationale={result.rationale} />
      ) : (
        <>
          <section>
            <p className="text-xs uppercase tracking-wide text-ink-faint mb-3">
              {result.ranked_matters.length} ranked {result.ranked_matters.length === 1 ? "match" : "matches"}
            </p>
            <div className="space-y-3">
              {result.ranked_matters.map((m) => (
                <RankedMatterCard key={m.matter_id} matter={m} top={m.rank === 1} />
              ))}
            </div>
          </section>

          {result.top_matter && (
            <section>
              <Tabs defaultValue="comparison">
                <TabsList>
                  <TabsTrigger value="comparison">Comparison</TabsTrigger>
                  <TabsTrigger value="reusability">Reusability</TabsTrigger>
                  <TabsTrigger value="reliability">
                    Reliability
                    {result.reliability.length > 0 && (
                      <span className="ml-1.5 rounded-full bg-black/[0.06] px-1.5 text-[10px]">
                        {result.reliability.length}
                      </span>
                    )}
                  </TabsTrigger>
                </TabsList>

                <div className="pt-6">
                  <TabsContent value="comparison">
                    {result.comparison ? (
                      <ComparisonView comparison={result.comparison} documents={documents} />
                    ) : (
                      <p className="text-sm text-ink-faint">Comparison unavailable (degraded mode).</p>
                    )}
                  </TabsContent>

                  <TabsContent value="reusability">
                    {result.reusability ? (
                      <ReusabilityBreakdownView breakdown={result.reusability} documents={documents} />
                    ) : (
                      <p className="text-sm text-ink-faint">Reusability assessment unavailable (degraded mode).</p>
                    )}
                  </TabsContent>

                  <TabsContent value="reliability">
                    {result.reliability.length === 0 ? (
                      <p className="text-sm text-ink-faint">
                        No authorities were relied upon in the matched matter, or reliability checking is
                        unavailable in degraded mode.
                      </p>
                    ) : (
                      <div className="space-y-4">
                        {result.reliability.map((outcome) => (
                          <ReliabilityReasoningPanel
                            key={outcome.authority_id}
                            queryLogId={result.query_log_id}
                            outcome={outcome}
                            documents={documents}
                          />
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </div>
              </Tabs>
            </section>
          )}
        </>
      )}
    </motion.div>
  );
}

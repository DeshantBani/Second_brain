"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationThread } from "@/components/draft/ConversationThread";
import { GatheredRequirementsCard } from "@/components/draft/GatheredRequirementsCard";
import { DraftView } from "@/components/draft/DraftView";
import { AgentTraceLoader } from "@/components/query/AgentTraceLoader";
import { api, ApiError } from "@/lib/api";
import type { DraftingSessionOut } from "@/lib/types";

export default function DraftSessionPage() {
  const params = useParams<{ id: string }>();
  const [session, setSession] = useState<DraftingSessionOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    api
      .getDraftingSession(params.id)
      .then(setSession)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this session."));
  }, [params.id]);

  const submitAnswer = async (e: FormEvent) => {
    e.preventDefault();
    if (!session || !answer.trim()) return;
    setSending(true);
    setError(null);
    try {
      const updated = await api.sendDraftingMessage(session.id, answer);
      setSession(updated);
      setAnswer("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send that answer.");
    } finally {
      setSending(false);
    }
  };

  const handleGenerateDraft = async () => {
    if (!session) return;
    setDrafting(true);
    setError(null);
    try {
      const updated = await api.generateDraft(session.id);
      setSession(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not generate the draft.");
    } finally {
      setDrafting(false);
    }
  };

  if (error && !session) {
    return <p className="text-sm text-verdict-red text-center py-16">{error}</p>;
  }

  if (!session) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <p className="text-xs uppercase tracking-wide text-ink-faint mb-1.5">Case brief</p>
        <p className="font-serif text-[15px] text-ink leading-snug">{session.case_brief}</p>
        {session.degraded_mode && (
          <Badge variant="amber" className="mt-2">
            Degraded mode — the reasoning engine was unavailable at some point in this session
          </Badge>
        )}
      </div>

      {session.conversation.length > 0 && <ConversationThread turns={session.conversation} />}

      {session.status === "gathering" && (
        <form onSubmit={submitAnswer} className="flex items-center gap-2">
          <Input value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Type your answer…" disabled={sending} />
          <Button type="submit" disabled={sending || !answer.trim()}>
            {sending ? "Sending…" : "Send"}
          </Button>
        </form>
      )}

      {session.status === "ready" && session.gathered_requirements && (
        <div className="space-y-4">
          <GatheredRequirementsCard requirements={session.gathered_requirements} />
          <Button onClick={handleGenerateDraft} disabled={drafting}>
            <Sparkles size={14} />
            {drafting ? "Drafting…" : "Generate draft"}
          </Button>
          {drafting && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-lg border border-border bg-paper-raised p-5">
              <AgentTraceLoader done={false} />
            </motion.div>
          )}
        </div>
      )}

      {session.status === "drafted" && session.draft_sections && (
        <div className="space-y-4">
          {session.gathered_requirements && <GatheredRequirementsCard requirements={session.gathered_requirements} />}
          <DraftView sections={session.draft_sections} templateStructure={session.template_structure} caseBrief={session.case_brief} />
        </div>
      )}

      {error && <p className="text-sm text-verdict-red">{error}</p>}
    </div>
  );
}

"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { DocumentUpload } from "@/components/shared/DocumentUpload";
import { api, ApiError } from "@/lib/api";
import { appendExtractedText } from "@/lib/format";

export default function NewDraftPage() {
  const router = useRouter();
  const [caseBrief, setCaseBrief] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const session = await api.startDraftingSession(caseBrief);
      router.push(`/draft/${session.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start this drafting session.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="font-display text-2xl text-ink mb-1.5">New draft</h1>
        <p className="text-sm text-ink-muted">
          Describe the case in your own words - parties, what happened, and what you want to achieve - or
          upload a document (a memo, notes, correspondence). The more detail you give here, the fewer
          follow-up questions you&apos;ll be asked, and the more precisely the draft will be grounded in your
          facts.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <DocumentUpload
          label="Upload case document"
          onExtracted={(text, filename) => setCaseBrief((prev) => appendExtractedText(prev, text, filename))}
        />
        <Textarea
          value={caseBrief}
          onChange={(e) => setCaseBrief(e.target.value)}
          required
          rows={10}
          placeholder="e.g. Our client X entered into an agreement with Y for... A dispute arose when... We believe... We want to..."
          className="font-serif text-[15px]"
        />
        {error && <p className="text-sm text-verdict-red">{error}</p>}
        <Button type="submit" disabled={loading || !caseBrief.trim()}>
          <Sparkles size={14} />
          {loading ? "Starting…" : "Continue"}
        </Button>
      </form>
    </div>
  );
}

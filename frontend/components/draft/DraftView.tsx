"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Check, Copy, SearchCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { DraftedSectionOut, TemplateStructureOut } from "@/lib/types";

export function DraftView({
  sections,
  templateStructure,
  caseBrief,
}: {
  sections: DraftedSectionOut[];
  templateStructure: TemplateStructureOut | null;
  caseBrief: string;
}) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  const copyAll = async () => {
    const text = sections.map((s) => `${s.section_name.toUpperCase()}\n\n${s.content}`).join("\n\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable - not critical, the text is still visible/selectable on the page
    }
  };

  const sendToProofread = () => {
    const text = sections.map((s) => `${s.section_name.toUpperCase()}\n\n${s.content}`).join("\n\n\n");
    try {
      sessionStorage.setItem("proofread_prefill", JSON.stringify({ draft_text: text, case_brief: caseBrief }));
    } catch {
      // ignore - proofread page will just start blank
    }
    router.push("/proofread");
  };

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-verdict-amber/30 bg-verdict-amber-bg px-4 py-3 flex items-start gap-2">
        <AlertTriangle size={15} className="text-verdict-amber shrink-0 mt-0.5" />
        <p className="text-xs text-ink">
          AI-drafted — review every section, verify all facts, dates, and figures, and confirm forum/jurisdiction
          details before filing. This is a starting point, not a finished, filing-ready document.
        </p>
      </div>

      {templateStructure && (
        <p className="text-xs text-ink-faint">
          Format: {templateStructure.grounded_in_sources ? "derived from a live web reference" : "standard convention (no usable web reference found)"} — {templateStructure.notes}
        </p>
      )}

      <div className="flex items-center gap-2">
        <Button size="sm" variant="outline" onClick={copyAll}>
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? "Copied" : "Copy full draft"}
        </Button>
        <Button size="sm" variant="outline" onClick={sendToProofread}>
          <SearchCheck size={13} />
          Send to proofreading
        </Button>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {sections.map((s, i) => (
            <div key={i}>
              {i > 0 && <Separator className="mb-6" />}
              <Badge variant="outline" className="mb-2 font-mono uppercase tracking-wide">
                {s.section_name}
              </Badge>
              <p className="font-serif text-[15px] leading-relaxed text-ink whitespace-pre-wrap">{s.content}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

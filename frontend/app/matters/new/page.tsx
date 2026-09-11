"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { DocumentUpload } from "@/components/shared/DocumentUpload";
import { api, ApiError } from "@/lib/api";
import { appendExtractedText } from "@/lib/format";

const DOC_TYPES = ["memo", "email", "contract", "pleading", "due_diligence", "note"];

export default function NewMatterPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [docTitle, setDocTitle] = useState("Ingested Report");
  const [docType, setDocType] = useState("memo");
  const [openedDate, setOpenedDate] = useState("");
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.createMatter({
        title,
        client_name: clientName,
        doc_title: docTitle || "Ingested Report",
        doc_type: docType,
        opened_date: openedDate || null,
        raw_text: rawText,
      });
      router.push(`/matters/${result.matter_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not ingest this matter.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="font-display text-2xl text-ink mb-1.5">New matter</h1>
        <p className="text-sm text-ink-muted">
          Paste a past matter&apos;s document below. The fingerprint agent will classify its jurisdiction,
          practice area, and clause tags into the same controlled vocabulary the retrieval funnel already
          uses, and scan it for case-law citations to populate the Authorities tab automatically.
        </p>
      </div>

      <form onSubmit={submit} className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Matter title</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Client X - Termination of Supply Agreement" />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Client name</label>
            <Input value={clientName} onChange={(e) => setClientName(e.target.value)} required placeholder="e.g. Client X Pvt. Ltd." />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Document title</label>
            <Input value={docTitle} onChange={(e) => setDocTitle(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Document type</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full rounded border border-border bg-paper-raised px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              {DOC_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Opened date (optional)</label>
            <Input type="date" value={openedDate} onChange={(e) => setOpenedDate(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-ink-muted mb-1.5">
            Document text
          </label>
          <div className="mb-2">
            <DocumentUpload
              label="Upload document (PDF/DOCX/TXT)"
              addPageMarkers
              onExtracted={(text, filename) => setRawText((prev) => appendExtractedText(prev, text, filename))}
            />
          </div>
          <Textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            required
            rows={14}
            placeholder={
              "Paste the memo, judgment report, or other document text here.\n\n" +
              "Optional: mark page breaks with a line reading exactly \"## PAGE 2\", \"## PAGE 3\", etc. " +
              "(page 1 is assumed for anything before the first marker). Paragraphs are separated by a blank line - " +
              "this is what lets every citation in the app link back to an exact page and paragraph."
            }
            className="font-mono text-xs"
          />
        </div>

        {error && <p className="text-sm text-verdict-red">{error}</p>}

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={loading}>
            <Sparkles size={14} />
            {loading ? "Ingesting…" : "Ingest & analyze"}
          </Button>
          {loading && (
            <span className="text-xs text-ink-faint">
              Extracting the issue fingerprint and scanning for citations - this takes a few seconds…
            </span>
          )}
        </div>

        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Card>
              <CardContent className="pt-4 text-xs text-ink-muted">
                Running the same fingerprint pipeline every matter in the archive goes through, then checking
                the text for case-law citations against the active CaseLawProvider.
              </CardContent>
            </Card>
          </motion.div>
        )}
      </form>
    </div>
  );
}

"use client";

import { FormEvent, useState } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Dialog, DialogBody, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { api, ApiError } from "@/lib/api";
import type { IngestDocumentResponse } from "@/lib/types";

const DOC_TYPES = ["memo", "email", "contract", "pleading", "due_diligence", "note"];

export function AddDocumentDialog({
  matterId,
  open,
  onClose,
  onIngested,
}: {
  matterId: string;
  open: boolean;
  onClose: () => void;
  onIngested: (result: IngestDocumentResponse) => void;
}) {
  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState("memo");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.ingestDocument({ matter_id: matterId, title, doc_type: docType, text });
      onIngested(result);
      setTitle("");
      setText("");
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not ingest this document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} className="max-w-xl">
      <DialogHeader>
        <DialogTitle>Add document</DialogTitle>
        <p className="text-xs text-ink-muted mt-1.5">
          Re-runs the fingerprint over every document in this matter combined, and scans this new document for
          case-law citations to add to the Authorities tab.
        </p>
      </DialogHeader>
      <form onSubmit={submit}>
        <DialogBody className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-ink-muted mb-1.5">Title</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="e.g. Advisory Memo - Follow-up" />
            </div>
            <div>
              <label className="block text-xs font-medium text-ink-muted mb-1.5">Type</label>
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
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-1.5">Document text</label>
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
              rows={10}
              placeholder={'Paste the document text. Optional "## PAGE 2" markers control page numbering.'}
              className="font-mono text-xs"
            />
          </div>
          {error && <p className="text-xs text-verdict-red">{error}</p>}
        </DialogBody>
        <DialogFooter>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" size="sm" disabled={loading}>
            <Sparkles size={13} />
            {loading ? "Ingesting…" : "Ingest & analyze"}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

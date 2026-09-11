"use client";

import { ChangeEvent, useRef, useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

/** Shared upload affordance for every free-text intake surface in the app (case
 * brief, new-matter/add-document text, proofreading draft text) - lets a lawyer
 * upload a PDF/DOCX/TXT/MD instead of pasting. Extraction happens server-side
 * (services/text_extraction.py); this component only handles the picker + calling
 * onExtracted with the resulting text. No OCR - a scanned/image-only PDF surfaces a
 * clear error instead of silently extracting nothing. */
export function DocumentUpload({
  onExtracted,
  addPageMarkers = false,
  label = "Upload document",
}: {
  onExtracted: (text: string, filename: string) => void;
  addPageMarkers?: boolean;
  label?: string;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const result = await api.extractText(file, addPageMarkers);
      onExtracted(result.text, result.filename);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not read this file.");
    } finally {
      setLoading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
        onChange={handleChange}
        className="hidden"
        id={`doc-upload-${label.replace(/\s+/g, "-")}`}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
        {loading ? "Reading…" : label}
      </Button>
      <p className="text-[11px] text-ink-faint">PDF, DOCX, TXT, or MD - no scanned/image-only PDFs</p>
      {error && <p className="text-xs text-verdict-red">{error}</p>}
    </div>
  );
}

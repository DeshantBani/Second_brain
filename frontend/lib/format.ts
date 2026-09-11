export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-IN", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function titleCase(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Appends text extracted from an uploaded document to an existing textarea value,
 * with a small header noting where it came from - used everywhere DocumentUpload is
 * wired in, so uploading accumulates rather than silently overwriting what's typed. */
export function appendExtractedText(existing: string, extracted: string, filename: string): string {
  const header = `--- Uploaded: ${filename} ---`;
  return existing.trim() ? `${existing}\n\n${header}\n${extracted}` : `${header}\n${extracted}`;
}

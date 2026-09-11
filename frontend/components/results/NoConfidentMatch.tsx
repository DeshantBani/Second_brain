import { SearchX } from "lucide-react";

export function NoConfidentMatch({ rationale }: { rationale: string }) {
  return (
    <div className="flex flex-col items-center text-center py-16 px-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-black/[0.05] text-ink-muted mb-4">
        <SearchX size={20} />
      </div>
      <h2 className="font-display text-xl text-ink mb-2">No confident match in the archive</h2>
      <p className="text-sm text-ink-muted font-serif max-w-md">{rationale}</p>
    </div>
  );
}

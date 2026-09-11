"use client";

import { KeyboardEvent, useState } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/cn";

export function QueryBox({
  value,
  onChange,
  onSubmit,
  loading,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
}) {
  const [focused, setFocused] = useState(false);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !loading) onSubmit();
    }
  };

  return (
    <div
      className={cn(
        "rounded-lg border bg-paper-raised shadow-paper transition-shadow duration-200",
        focused ? "border-ink/40 shadow-raised" : "border-border"
      )}
    >
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        rows={3}
        placeholder="Describe the legal problem in plain language — jurisdiction, contract structure, and what's happening now…"
        className="w-full resize-none bg-transparent px-5 pt-4 pb-2 text-[15px] leading-relaxed text-ink placeholder:text-ink-faint focus:outline-none font-serif"
      />
      <div className="flex items-center justify-between px-5 pb-3">
        <span className="text-xs text-ink-faint">Enter to search · Shift+Enter for a new line</span>
        <button
          onClick={onSubmit}
          disabled={!value.trim() || loading}
          aria-label="Submit query"
          className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-paper disabled:opacity-30 disabled:cursor-not-allowed hover:bg-ink/90 transition-colors"
        >
          <ArrowUp size={16} />
        </button>
      </div>
    </div>
  );
}

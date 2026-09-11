import { cn } from "@/lib/cn";
import type { ConversationTurn } from "@/lib/types";

export function ConversationThread({ turns }: { turns: ConversationTurn[] }) {
  return (
    <div className="space-y-3">
      {turns.map((t, i) => (
        <div key={i} className={cn("flex", t.role === "user" ? "justify-end" : "justify-start")}>
          <div
            className={cn(
              "max-w-[85%] rounded-lg px-4 py-2.5 text-sm",
              t.role === "user" ? "bg-ink text-paper" : "bg-paper-raised border border-border text-ink font-serif"
            )}
          >
            {t.content}
          </div>
        </div>
      ))}
    </div>
  );
}

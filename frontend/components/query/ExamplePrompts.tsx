"use client";

export const EXAMPLE_PROMPTS = [
  {
    label: "Supply agreement termination (the Section 15 scenario)",
    text: "Our client wants to exit a five year manufacturing supply agreement governed by Indian law. The contract has a termination for convenience clause with a thirty day cure period. Counterparty is threatening damages. Have we advised on this before?",
  },
  {
    label: "Distribution agreement exclusivity breach",
    text: "A distributor in Karnataka has been selling outside its assigned territory in breach of an exclusivity clause. Can we terminate immediately without a cure period, and have we handled something like this before?",
  },
  {
    label: "EPC arbitration - award challenge",
    text: "We are considering a Section 34 challenge to an arbitral award in an EPC dispute over a performance guarantee. What is our track record on similar public-policy challenges?",
  },
];

export function ExamplePrompts({ onSelect }: { onSelect: (text: string) => void }) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {EXAMPLE_PROMPTS.map((p) => (
        <button
          key={p.label}
          onClick={() => onSelect(p.text)}
          className="rounded-full border border-border bg-paper-raised px-3.5 py-1.5 text-xs text-ink-muted hover:text-ink hover:border-ink/30 transition-colors"
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

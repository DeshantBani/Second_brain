import { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "default" | "accent" | "outline" | "green" | "amber" | "red" | "grey";

const variantClasses: Record<Variant, string> = {
  default: "bg-black/[0.05] text-ink border border-transparent",
  accent: "bg-accent-soft text-accent border border-transparent",
  outline: "bg-transparent text-ink-muted border border-border",
  green: "bg-verdict-green-bg text-verdict-green border border-transparent",
  amber: "bg-verdict-amber-bg text-verdict-amber border border-transparent",
  red: "bg-verdict-red-bg text-verdict-red border border-transparent",
  grey: "bg-verdict-grey-bg text-verdict-grey border border-transparent",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium tracking-tight",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}

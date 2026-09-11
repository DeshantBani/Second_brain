import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded border border-border bg-paper-raised px-3 py-2 text-sm text-ink placeholder:text-ink-faint",
        "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded border border-border bg-paper-raised px-3 py-2 text-sm text-ink placeholder:text-ink-faint resize-none",
        "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

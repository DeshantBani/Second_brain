"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import { TopNav } from "./TopNav";
import { getToken } from "@/lib/auth";
import { api } from "@/lib/api";

const BARE_PREFIXES = ["/login", "/addin"];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isBare = BARE_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
  const [checkedAuth, setCheckedAuth] = useState(isBare);
  const [degraded, setDegraded] = useState<{ provider: string } | null>(null);

  useEffect(() => {
    if (isBare) return;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setCheckedAuth(true);
  }, [isBare, pathname, router]);

  useEffect(() => {
    api
      .health()
      .then((h) => {
        if (!h.llm_configured) setDegraded({ provider: h.llm_provider });
      })
      .catch(() => {
        // health endpoint unreachable - surface nothing extra, individual requests will fail loudly enough
      });
  }, []);

  if (isBare) return <>{children}</>;
  if (!checkedAuth) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      {degraded && (
        <div className="bg-verdict-amber-bg border-b border-verdict-amber/20 px-6 py-2 text-xs text-verdict-amber flex items-center justify-center gap-2">
          <AlertTriangle size={13} />
          {degraded.provider} is not configured on the backend - retrieval and reasoning are running in
          degraded mode (structured/vector filtering only, no agent reasoning).
        </div>
      )}
      <main className="flex-1 mx-auto w-full max-w-6xl px-6 py-8">{children}</main>
      <footer className="border-t border-border py-4 text-center text-xs text-ink-faint">
        Second Brain - internal knowledge archive. Every reliability verdict is a prompt to verify, never a clearance.
      </footer>
    </div>
  );
}

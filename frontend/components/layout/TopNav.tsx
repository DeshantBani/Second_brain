"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BookMarked, History, LayoutList, ScrollText, ShieldCheck, Terminal, LogOut } from "lucide-react";
import { clearSession, getStoredUser, StoredUser } from "@/lib/auth";
import { initials } from "@/lib/format";
import { cn } from "@/lib/cn";

const NAV_ITEMS = [
  { href: "/", label: "Query", icon: BookMarked },
  { href: "/matters", label: "Matters", icon: LayoutList },
  { href: "/history", label: "History", icon: History },
];

const ADMIN_NAV_ITEMS = [
  { href: "/audit", label: "Audit Log", icon: ScrollText },
  { href: "/admin/authorities", label: "Authorities", icon: ShieldCheck },
  { href: "/admin/agent-calls", label: "Agent Calls", icon: Terminal },
];

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  const items = user?.role === "admin" ? [...NAV_ITEMS, ...ADMIN_NAV_ITEMS] : NAV_ITEMS;

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-paper/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="font-display text-lg tracking-tight text-ink">Second Brain</span>
          <span className="hidden sm:inline text-[11px] uppercase tracking-[0.14em] text-ink-faint mt-0.5">
            Knowledge Archive
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {items.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors",
                  active ? "bg-black/[0.05] text-ink" : "text-ink-muted hover:text-ink"
                )}
              >
                <item.icon size={15} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {user && (
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col items-end leading-tight">
              <span className="text-sm text-ink font-medium">{user.display_name}</span>
              <span className="text-xs text-ink-faint">{user.role}</span>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-paper text-xs font-semibold">
              {initials(user.display_name)}
            </div>
            <button
              onClick={handleLogout}
              aria-label="Log out"
              className="text-ink-muted hover:text-ink transition-colors"
            >
              <LogOut size={17} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

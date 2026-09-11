"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ScrollText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";
import { setSession } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { label: "Meera Nair (lawyer1)", email: "lawyer1@secondbrain.test", password: "lawyer123" },
  { label: "Arjun Rao (lawyer2)", email: "lawyer2@secondbrain.test", password: "lawyer123" },
  { label: "Firm Admin", email: "admin@secondbrain.test", password: "admin123" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("lawyer1@secondbrain.test");
  const [password, setPassword] = useState("lawyer123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setSession(res.access_token, {
        user_id: res.user_id,
        email: res.email,
        display_name: res.display_name,
        role: res.role,
      });
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center paper-texture px-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-sm"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-ink text-paper mb-4">
            <ScrollText size={20} />
          </div>
          <h1 className="font-display text-2xl text-ink tracking-tight">Second Brain</h1>
          <p className="text-sm text-ink-muted mt-1">Sign in to the knowledge archive</p>
        </div>

        <Card>
          <CardContent className="pt-5">
            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-ink-muted mb-1.5">Email</label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-muted mb-1.5">Password</label>
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
              {error && <p className="text-xs text-verdict-red">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="mt-6 rounded-lg border border-border bg-paper-raised/60 p-4">
          <p className="text-xs font-medium text-ink-muted mb-2">Demo accounts</p>
          <div className="space-y-1.5">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => {
                  setEmail(acc.email);
                  setPassword(acc.password);
                }}
                className="block w-full text-left text-xs text-ink-muted hover:text-ink transition-colors font-mono"
              >
                {acc.label} <span className="text-ink-faint">— {acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

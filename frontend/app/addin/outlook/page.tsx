"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail } from "lucide-react";
import { QueryBox } from "@/components/query/QueryBox";
import { Card, CardContent } from "@/components/ui/card";
import { getToken } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";

/** Scaffolded Office task-pane route (build plan Section 9 / Phase 5 fast-follow).
 * A real integration would authenticate via Office.context.ui.displayDialogAsync
 * against /addin/session and receive the JWT back via messageParent - this route
 * reuses the exact same components and API client as the web app so that wiring, when
 * built, is additive rather than a rewrite. */
export default function OutlookAddinPage() {
  const router = useRouter();
  const [text, setText] = useState(
    "Counterparty is threatening damages under our supply agreement before the cure period has even run — have we seen this before?"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!getToken()) {
      setError("Not signed in. In a full integration this task pane would open a sign-in dialog via Office.context.ui.displayDialogAsync.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.submitQuery(text, "outlook");
      sessionStorage.setItem(`query_result_${result.query_log_id}`, JSON.stringify(result));
      router.push(`/query/${result.query_log_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the reasoning engine.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-10 px-4">
      <div className="flex items-center gap-2 mb-4 text-ink-muted">
        <Mail size={16} />
        <p className="text-xs uppercase tracking-wide">Outlook task pane (scaffold)</p>
      </div>
      <Card className="mb-4">
        <CardContent className="pt-4 text-xs text-ink-muted">
          This route is a structural stub — it shares the same QueryBox and API client as the main app, but is not
          yet wired to Office.js. A real add-in would seed this box from the open email's body automatically.
        </CardContent>
      </Card>
      <QueryBox value={text} onChange={setText} onSubmit={submit} loading={loading} />
      {error && <p className="text-xs text-verdict-red mt-3">{error}</p>}
    </div>
  );
}

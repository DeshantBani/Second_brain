"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileEdit } from "lucide-react";
import { QueryBox } from "@/components/query/QueryBox";
import { Card, CardContent } from "@/components/ui/card";
import { getToken } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";

/** Scaffolded Word task-pane route - see the note in app/addin/outlook/page.tsx. A real
 * integration's "insert into draft" action would route through the same ReviewGate
 * confirmation used on the web app before any cited text reaches the document. */
export default function WordAddinPage() {
  const router = useRouter();
  const [text, setText] = useState("");
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
      const result = await api.submitQuery(text, "word");
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
        <FileEdit size={16} />
        <p className="text-xs uppercase tracking-wide">Word task pane (scaffold)</p>
      </div>
      <Card className="mb-4">
        <CardContent className="pt-4 text-xs text-ink-muted">
          This route is a structural stub. A full integration would let a lawyer query the archive without
          leaving the draft, and insert reusable language directly — carrying its source citation and requiring
          the same human-verification Review Gate used on the web app.
        </CardContent>
      </Card>
      <QueryBox value={text} onChange={setText} onSubmit={submit} loading={loading} />
      {error && <p className="text-xs text-verdict-red mt-3">{error}</p>}
    </div>
  );
}

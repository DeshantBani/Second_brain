"use client";

import { useState } from "react";
import { FileText, Plus, ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfidentialityTierPill } from "@/components/shared/ConfidentialityTierPill";
import { DocumentViewer } from "@/components/citations/DocumentViewer";
import { AddDocumentDialog } from "./AddDocumentDialog";
import { FingerprintCard } from "./FingerprintCard";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { DocumentDetail, IngestDocumentResponse, MatterDetail } from "@/lib/types";

const STATUS_ICON: Record<string, typeof ShieldCheck> = {
  good_law: ShieldCheck,
  doubted: ShieldAlert,
  distinguished: ShieldAlert,
  overruled: ShieldAlert,
};

const STATUS_VARIANT: Record<string, "green" | "amber" | "red"> = {
  good_law: "green",
  doubted: "amber",
  distinguished: "amber",
  overruled: "red",
};

export function MatterDetailTabs({ matter, onChanged }: { matter: MatterDetail; onChanged?: () => void }) {
  const [viewerDoc, setViewerDoc] = useState<DocumentDetail | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [addDocOpen, setAddDocOpen] = useState(false);
  const [lastIngest, setLastIngest] = useState<IngestDocumentResponse | null>(null);

  const openDocument = async (documentId: string) => {
    const detail = (await api.getDocument(matter.id, documentId)) as DocumentDetail;
    setViewerDoc(detail);
    setViewerOpen(true);
  };

  const handleIngested = (result: IngestDocumentResponse) => {
    setLastIngest(result);
    onChanged?.();
  };

  return (
    <>
      <Tabs defaultValue="documents">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="fingerprint">Fingerprint</TabsTrigger>
          <TabsTrigger value="authorities">Authorities</TabsTrigger>
        </TabsList>

        <div className="pt-6">
          <TabsContent value="documents">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs uppercase tracking-wide text-ink-faint">{matter.documents.length} documents</p>
              <Button size="sm" variant="outline" onClick={() => setAddDocOpen(true)}>
                <Plus size={13} />
                Add document
              </Button>
            </div>
            {lastIngest && (
              <div className="mb-3 rounded border border-verdict-green/30 bg-verdict-green-bg px-3 py-2 text-xs text-verdict-green">
                Ingested. {lastIngest.citations_linked.length > 0
                  ? `Linked ${lastIngest.citations_linked.length} citation(s) to the Authorities tab.`
                  : "No case-law citations were found in this document."}
              </div>
            )}
            <div className="space-y-2">
              {matter.documents.map((d) => (
                <button key={d.id} onClick={() => openDocument(d.id)} className="w-full text-left">
                  <Card className="hover:border-ink/30 transition-colors">
                    <CardContent className="pt-4 pb-4 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <FileText size={16} className="text-ink-faint shrink-0" />
                        <div>
                          <p className="text-sm text-ink font-medium">{d.title}</p>
                          <p className="text-xs text-ink-faint">
                            {d.doc_type.replace(/_/g, " ")} · added {formatDate(d.created_at)}
                          </p>
                        </div>
                      </div>
                      <ConfidentialityTierPill tier={d.confidentiality_tier} />
                    </CardContent>
                  </Card>
                </button>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="fingerprint">
            {matter.fingerprint ? (
              <FingerprintCard fingerprint={matter.fingerprint} />
            ) : (
              <p className="text-sm text-ink-faint">No fingerprint generated for this matter yet.</p>
            )}
          </TabsContent>

          <TabsContent value="authorities">
            {matter.authorities.length === 0 ? (
              <p className="text-sm text-ink-faint">No authorities relied upon in this matter.</p>
            ) : (
              <div className="space-y-2">
                {matter.authorities.map((a) => {
                  const Icon = STATUS_ICON[a.status] || ShieldQuestion;
                  return (
                    <Card key={a.id}>
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-start justify-between gap-3 mb-1.5">
                          <p className="font-mono text-xs text-ink">{a.citation}</p>
                          <Badge variant={STATUS_VARIANT[a.status] || "grey"}>
                            <Icon size={11} />
                            {a.status.replace(/_/g, " ")}
                          </Badge>
                        </div>
                        <p className="text-xs text-ink-faint mb-1.5">
                          {a.court}, {a.year} · cited at p.{a.cited_at_page} ¶{a.cited_at_paragraph}
                        </p>
                        <p className="text-sm text-ink-muted font-serif">{a.relied_upon_for}</p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </div>
      </Tabs>

      <DocumentViewer open={viewerOpen} onClose={() => setViewerOpen(false)} document={viewerDoc} />
      <AddDocumentDialog
        matterId={matter.id}
        open={addDocOpen}
        onClose={() => setAddDocOpen(false)}
        onIngested={handleIngested}
      />
    </>
  );
}

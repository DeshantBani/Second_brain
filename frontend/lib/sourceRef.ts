import type { QueryTopMatterDocument, SourceRef } from "./types";

export interface ResolvedSource {
  documentTitle: string;
  documentId: string;
  page: number;
  paragraph: number;
  text: string;
  found: boolean;
}

export function resolveSourceRef(documents: QueryTopMatterDocument[], ref: SourceRef): ResolvedSource {
  const doc = documents.find((d) => d.id === ref.document_id);
  if (!doc) {
    return { documentTitle: "Unknown document", documentId: ref.document_id, page: ref.page, paragraph: ref.paragraph, text: ref.quote, found: false };
  }
  const entry = doc.page_map.find((p) => p.page === ref.page && p.paragraph === ref.paragraph);
  return {
    documentTitle: doc.title,
    documentId: doc.id,
    page: ref.page,
    paragraph: ref.paragraph,
    text: entry?.text || ref.quote,
    found: Boolean(entry),
  };
}

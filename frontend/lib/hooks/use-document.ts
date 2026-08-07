"use client"

import { useQuery } from "@tanstack/react-query"
import { getDocument } from "@/lib/api/documents"
import { isNotFoundError } from "@/lib/hooks/use-document-status"

/** Query key for a single document's detail record. Exported so callers can invalidate it. */
export function documentDetailKey(documentId: string | undefined) {
  return ["document-detail", documentId] as const
}

/**
 * Fetches one document's full record, including its extracted text.
 *
 * Deliberately does NOT poll. The detail payload carries the entire
 * extracted text, which can be hundreds of KB, and extraction is the first
 * ingestion stage - so a document that is still chunking or embedding
 * already has its text and re-pulling it every 2s would move real weight
 * over the wire for a status string. Callers that need live status pair
 * this with useDocumentStatusPolling (RF-29), which hits the small
 * /status endpoint, and refetch this query once the status turns terminal.
 *
 * A 404 is terminal, matching useDocumentStatusPolling: the backend 404s
 * both for a missing document and for one the caller doesn't own, and
 * neither becomes true on a retry.
 */
export function useDocumentDetail(documentId: string | undefined) {
  return useQuery({
    queryKey: documentDetailKey(documentId),
    queryFn: () => getDocument(documentId as string),
    enabled: !!documentId,
    retry: (failureCount, error) => !isNotFoundError(error) && failureCount < 3,
  })
}

"use client"

import { isAxiosError } from "axios"
import { useQuery } from "@tanstack/react-query"
import { getDocumentStatus } from "@/lib/api/documents"

const POLLING_INTERVAL_MS = 2000
const TERMINAL_STATUSES = new Set(["completed", "failed"])

/** Poll interval for a document's ingestion status: 2s while in-flight, stop once terminal. */
export function nextPollInterval(status: string | undefined): number | false {
  return TERMINAL_STATUSES.has(status ?? "") ? false : POLLING_INTERVAL_MS
}

/** A 404 means the document is gone - treat it as a terminal failure, never retry or re-poll it. */
export function isNotFoundError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 404
}

export function useDocumentStatusPolling(documentId: string | undefined) {
  return useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => getDocumentStatus(documentId as string),
    enabled: !!documentId,
    retry: (failureCount, error) => !isNotFoundError(error) && failureCount < 3,
    refetchInterval: (query) =>
      isNotFoundError(query.state.error) ? false : nextPollInterval(query.state.data?.status),
  })
}

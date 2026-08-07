"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, FileQuestion } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useDocumentDetail } from "@/lib/hooks/use-document"
import { isNotFoundError, useDocumentStatusPolling } from "@/lib/hooks/use-document-status"
import { DocumentDetailView } from "./components/document-detail-view"

const TERMINAL_STATUSES = new Set(["completed", "failed"])

function DetailSkeleton() {
  return (
    <div className="space-y-6" data-testid="detail-skeleton">
      <div className="space-y-2">
        <div className="h-8 w-1/3 animate-pulse rounded bg-muted" />
        <div className="h-4 w-1/4 animate-pulse rounded bg-muted" />
      </div>
      <div className="h-32 animate-pulse rounded-lg bg-muted" />
      <div className="h-40 animate-pulse rounded-lg bg-muted" />
    </div>
  )
}

function NotFoundState({ onBack }: { onBack: () => void }) {
  return (
    <Card data-testid="detail-not-found">
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <FileQuestion className="h-8 w-8 text-muted-foreground" />
        <div className="space-y-1">
          <p className="font-medium">Document not found</p>
          {/* The backend returns 404 rather than 403 for a document the
              caller doesn't own, so a client id can't be probed for
              existence. That means "deleted" and "not yours" look
              identical here, and the copy shouldn't claim to know which. */}
          <p className="text-sm text-muted-foreground">
            It may have been deleted, or it belongs to a client you don&apos;t have access to.
          </p>
        </div>
        <Button variant="outline" onClick={onBack}>
          Go back
        </Button>
      </CardContent>
    </Card>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card data-testid="detail-error">
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <p className="font-medium">Could not load this document</p>
        <p className="text-sm text-muted-foreground">
          Something went wrong reaching the server. Please try again.
        </p>
        <Button variant="outline" onClick={onRetry}>
          Retry
        </Button>
      </CardContent>
    </Card>
  )
}

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  // Next 16 delivers route params as a promise; unwrap it in the client
  // component with React.use.
  const { id } = React.use(params)
  const router = useRouter()

  const detail = useDocumentDetail(id)
  // The detail payload carries the whole extracted text, so live status
  // comes from the small /status endpoint (RF-29) rather than by re-pulling
  // the document every couple of seconds.
  const polled = useDocumentStatusPolling(id)

  const polledStatus = polled.data?.status
  const cachedStatus = detail.data?.status
  const status = polledStatus ?? cachedStatus ?? "uploaded"

  const { refetch: refetchDetail } = detail
  React.useEffect(() => {
    // Ingestion just finished, but the cached detail record predates that
    // and still has no extracted text - pull it once more. The condition
    // clears itself as soon as the refetch lands, so this fires once per
    // transition rather than on every poll.
    if (!polledStatus || !cachedStatus) return
    if (TERMINAL_STATUSES.has(polledStatus) && !TERMINAL_STATUSES.has(cachedStatus)) {
      void refetchDetail()
    }
  }, [polledStatus, cachedStatus, refetchDetail])

  // Browser back is what preserves the previous screen's state - the search
  // results a card was clicked from stay in the TanStack Query cache, so
  // returning re-renders them instead of re-running the search (RF-109).
  const handleBack = React.useCallback(() => router.back(), [router])

  const notFound = isNotFoundError(detail.error) || isNotFoundError(polled.error)

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Button
        variant="ghost"
        onClick={handleBack}
        className="-ml-2 h-8 px-2 text-muted-foreground hover:text-foreground"
        data-testid="detail-back"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      {notFound ? (
        <NotFoundState onBack={handleBack} />
      ) : detail.isError ? (
        <ErrorState onRetry={() => void refetchDetail()} />
      ) : detail.data ? (
        <DocumentDetailView document={detail.data} status={status} />
      ) : (
        <DetailSkeleton />
      )}
    </div>
  )
}

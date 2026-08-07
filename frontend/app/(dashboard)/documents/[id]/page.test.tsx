import { describe, it, expect, vi, beforeEach } from "vitest"
import { Suspense } from "react"
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import type { DocumentDetail } from "@/types/api"

const backMock = vi.fn()
vi.mock("next/navigation", () => ({
  useRouter: () => ({ back: backMock }),
}))

const useDocumentDetailMock = vi.fn()
vi.mock("@/lib/hooks/use-document", () => ({
  useDocumentDetail: (...args: unknown[]) => useDocumentDetailMock(...args),
}))

const useDocumentStatusPollingMock = vi.fn()
vi.mock("@/lib/hooks/use-document-status", () => ({
  useDocumentStatusPolling: (...args: unknown[]) => useDocumentStatusPollingMock(...args),
  isNotFoundError: (error: unknown) =>
    !!error &&
    typeof error === "object" &&
    (error as { response?: { status?: number } }).response?.status === 404,
}))

import DocumentDetailPage from "./page"

const notFoundError = { response: { status: 404 } }

function makeDocument(overrides: Partial<DocumentDetail> = {}): DocumentDetail {
  return {
    id: "doc-1",
    client_id: "client-1",
    user_id: "user-1",
    title: "Priya Sharma - Senior Backend Engineer",
    doc_type: "resume",
    file_name: "priya-sharma.pdf",
    file_size_kb: 148,
    mime_type: "application/pdf",
    status: "completed",
    extracted_text: "Resume body.",
    auto_tags: null,
    manual_tags: null,
    created_at: "2026-08-01T10:30:00Z",
    updated_at: "2026-08-01T10:32:00Z",
    deleted_at: null,
    ...overrides,
  }
}

/**
 * The page takes route params as a promise (Next 16) and unwraps them with
 * React.use, which suspends until the promise resolves. Next supplies the
 * boundary for that in the real app; the test supplies its own, and the
 * render has to happen inside an awaited act or the suspended tree never
 * flushes and the container stays empty.
 */
async function renderPage() {
  await act(async () => {
    render(
      <Suspense fallback={null}>
        <DocumentDetailPage params={Promise.resolve({ id: "doc-1" })} />
      </Suspense>
    )
  })
}

function detailResult(over: Record<string, unknown> = {}) {
  return { data: undefined, error: null, isError: false, refetch: vi.fn(), ...over }
}

function pollResult(over: Record<string, unknown> = {}) {
  return { data: undefined, error: null, ...over }
}

describe("DocumentDetailPage", () => {
  beforeEach(() => {
    backMock.mockReset()
    useDocumentDetailMock.mockReset()
    useDocumentStatusPollingMock.mockReset()
  })

  it("shows a skeleton while the document is loading", async () => {
    useDocumentDetailMock.mockReturnValue(detailResult())
    useDocumentStatusPollingMock.mockReturnValue(pollResult())

    await renderPage()

    expect(await screen.findByTestId("detail-skeleton")).toBeInTheDocument()
  })

  it("renders the document once it loads", async () => {
    useDocumentDetailMock.mockReturnValue(detailResult({ data: makeDocument() }))
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "completed" } }))

    await renderPage()

    expect(await screen.findByText("Priya Sharma - Senior Backend Engineer")).toBeInTheDocument()
    expect(screen.getByTestId("extracted-text")).toHaveTextContent("Resume body.")
  })

  it("shows a not-found state for a document that is missing or not the caller's", async () => {
    useDocumentDetailMock.mockReturnValue(detailResult({ error: notFoundError, isError: true }))
    useDocumentStatusPollingMock.mockReturnValue(pollResult())

    await renderPage()

    expect(await screen.findByTestId("detail-not-found")).toBeInTheDocument()
    // A 404 is not a transient error - it must not offer a retry.
    expect(screen.queryByTestId("detail-error")).not.toBeInTheDocument()
  })

  it("offers a retry on a non-404 failure", async () => {
    const refetch = vi.fn()
    useDocumentDetailMock.mockReturnValue(
      detailResult({ error: { response: { status: 500 } }, isError: true, refetch })
    )
    useDocumentStatusPollingMock.mockReturnValue(pollResult())

    await renderPage()

    fireEvent.click(await screen.findByRole("button", { name: "Retry" }))
    expect(refetch).toHaveBeenCalled()
  })

  it("prefers the polled status over the one on the cached detail record", async () => {
    useDocumentDetailMock.mockReturnValue(
      detailResult({ data: makeDocument({ status: "extracting", extracted_text: null }) })
    )
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "embedding" } }))

    await renderPage()

    expect(await screen.findByTestId("detail-status")).toHaveTextContent("Embedding")
    // Still ingesting, so the text area explains itself rather than sitting empty.
    expect(screen.getByTestId("extracted-text-pending")).toBeInTheDocument()
  })

  it("refetches the detail once ingestion finishes, so the extracted text arrives", async () => {
    const refetch = vi.fn()
    useDocumentDetailMock.mockReturnValue(
      detailResult({ data: makeDocument({ status: "chunking", extracted_text: null }), refetch })
    )
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "completed" } }))

    await renderPage()

    await waitFor(() => expect(refetch).toHaveBeenCalledTimes(1))
  })

  it("does not refetch while ingestion is still in flight", async () => {
    const refetch = vi.fn()
    useDocumentDetailMock.mockReturnValue(
      detailResult({ data: makeDocument({ status: "extracting", extracted_text: null }), refetch })
    )
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "chunking" } }))

    await renderPage()

    await screen.findByTestId("detail-status")
    expect(refetch).not.toHaveBeenCalled()
  })

  it("does not refetch when the cached record is already terminal", async () => {
    // Guards against a refetch loop: the effect's condition has to clear
    // itself once the fresh record lands.
    const refetch = vi.fn()
    useDocumentDetailMock.mockReturnValue(
      detailResult({ data: makeDocument({ status: "completed" }), refetch })
    )
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "completed" } }))

    await renderPage()

    await screen.findByTestId("detail-status")
    expect(refetch).not.toHaveBeenCalled()
  })

  it("goes back in history so the previous search results stay intact", async () => {
    useDocumentDetailMock.mockReturnValue(detailResult({ data: makeDocument() }))
    useDocumentStatusPollingMock.mockReturnValue(pollResult({ data: { status: "completed" } }))

    await renderPage()

    fireEvent.click(await screen.findByTestId("detail-back"))
    expect(backMock).toHaveBeenCalledTimes(1)
  })
})

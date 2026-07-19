import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

const getDocumentStatusMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  getDocumentStatus: (...args: unknown[]) => getDocumentStatusMock(...args),
}))

import { useDocumentStatusPolling, nextPollInterval, isNotFoundError } from "./use-document-status"

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe("nextPollInterval", () => {
  it("returns the polling interval for in-flight statuses", () => {
    expect(nextPollInterval("uploaded")).toBe(2000)
    expect(nextPollInterval("extracting")).toBe(2000)
    expect(nextPollInterval("chunking")).toBe(2000)
    expect(nextPollInterval("embedding")).toBe(2000)
    expect(nextPollInterval(undefined)).toBe(2000)
  })

  it("returns false for terminal statuses", () => {
    expect(nextPollInterval("completed")).toBe(false)
    expect(nextPollInterval("failed")).toBe(false)
  })
})

describe("useDocumentStatusPolling", () => {
  beforeEach(() => {
    getDocumentStatusMock.mockReset()
  })

  it("does not fetch when no documentId is given", () => {
    const { result } = renderHook(() => useDocumentStatusPolling(undefined), { wrapper })
    expect(getDocumentStatusMock).not.toHaveBeenCalled()
    expect(result.current.data).toBeUndefined()
  })

  it("fetches status once a documentId is given", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "extracting",
      created_at: "2026-07-19T00:00:00Z",
    })

    const { result } = renderHook(() => useDocumentStatusPolling("doc-1"), { wrapper })

    await waitFor(() => expect(result.current.data?.status).toBe("extracting"))
    expect(getDocumentStatusMock).toHaveBeenCalledWith("doc-1")
  })

  it("does not retry a 404 - the document is gone, so one failed fetch is terminal", async () => {
    getDocumentStatusMock.mockRejectedValue(
      Object.assign(new Error("Not Found"), { isAxiosError: true, response: { status: 404 } })
    )

    const { result } = renderHook(() => useDocumentStatusPolling("doc-missing"), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))
    // Give any (incorrect) retry a tick to fire before asserting call count.
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(getDocumentStatusMock).toHaveBeenCalledTimes(1)
  })
})

describe("isNotFoundError", () => {
  it("recognizes a 404 axios error", () => {
    const err = Object.assign(new Error("Not Found"), {
      isAxiosError: true,
      response: { status: 404 },
    })
    expect(isNotFoundError(err)).toBe(true)
  })

  it("returns false for other errors", () => {
    expect(isNotFoundError(new Error("boom"))).toBe(false)
    expect(
      isNotFoundError(
        Object.assign(new Error("Server Error"), { isAxiosError: true, response: { status: 500 } })
      )
    ).toBe(false)
  })
})

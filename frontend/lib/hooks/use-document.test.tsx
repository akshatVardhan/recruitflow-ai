import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

const getDocumentMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  getDocument: (...args: unknown[]) => getDocumentMock(...args),
}))

import { useDocumentDetail, documentDetailKey } from "./use-document"

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe("documentDetailKey", () => {
  it("namespaces the key by document id", () => {
    expect(documentDetailKey("doc-1")).toEqual(["document-detail", "doc-1"])
  })
})

describe("useDocumentDetail", () => {
  beforeEach(() => {
    getDocumentMock.mockReset()
  })

  it("does not fetch without a document id", () => {
    const { result } = renderHook(() => useDocumentDetail(undefined), { wrapper })
    expect(getDocumentMock).not.toHaveBeenCalled()
    expect(result.current.data).toBeUndefined()
  })

  it("fetches the document once an id is given", async () => {
    getDocumentMock.mockResolvedValueOnce({ id: "doc-1", status: "completed" })

    const { result } = renderHook(() => useDocumentDetail("doc-1"), { wrapper })

    await waitFor(() => expect(result.current.data?.id).toBe("doc-1"))
    expect(getDocumentMock).toHaveBeenCalledWith("doc-1")
  })

  it("does not poll - the detail payload carries the whole extracted text", async () => {
    getDocumentMock.mockResolvedValue({ id: "doc-1", status: "extracting" })

    const { result } = renderHook(() => useDocumentDetail("doc-1"), { wrapper })
    await waitFor(() => expect(result.current.data?.id).toBe("doc-1"))

    // Well past the 2s status-poll interval this query deliberately doesn't use.
    await new Promise((resolve) => setTimeout(resolve, 120))
    expect(getDocumentMock).toHaveBeenCalledTimes(1)
  })

  it("does not retry a 404 - the document is missing or not the caller's", async () => {
    getDocumentMock.mockRejectedValue(
      Object.assign(new Error("Not Found"), { isAxiosError: true, response: { status: 404 } })
    )

    const { result } = renderHook(() => useDocumentDetail("doc-missing"), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(getDocumentMock).toHaveBeenCalledTimes(1)
  })
})

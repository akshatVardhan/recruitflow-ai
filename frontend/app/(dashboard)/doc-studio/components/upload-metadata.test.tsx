import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { useForm } from "react-hook-form"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { UploadMetadataRow } from "./upload-metadata"
import type { QueueFormValues, UploadStatus } from "../schema"

const getDocumentStatusMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  getDocumentStatus: (...args: unknown[]) => getDocumentStatusMock(...args),
}))

function Harness({ status, documentId }: { status: UploadStatus; documentId?: string }) {
  const { control, register } = useForm<QueueFormValues>({
    defaultValues: {
      items: [
        { title: "resume", doc_type: "other", client_id: "11111111-1111-1111-1111-111111111111" },
      ],
    },
  })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <UploadMetadataRow
        index={0}
        control={control}
        register={register}
        fileName="resume.pdf"
        status={status}
        documentId={documentId}
        onRemove={() => {}}
        disabled={false}
      />
    </QueryClientProvider>
  )
}

describe("UploadMetadataRow ingestion status", () => {
  beforeEach(() => {
    getDocumentStatusMock.mockReset()
  })

  it("shows the local upload status when no documentId is set yet", () => {
    render(<Harness status="uploading" />)
    expect(screen.getByText("Uploading")).toBeInTheDocument()
    expect(getDocumentStatusMock).not.toHaveBeenCalled()
  })

  it("polls and shows the backend ingestion stage once a documentId is set", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "extracting",
      created_at: "2026-07-19T00:00:00Z",
    })

    render(<Harness status="uploaded" documentId="doc-1" />)

    await waitFor(() => expect(screen.getByText("Extracting")).toBeInTheDocument())
    expect(screen.getByTestId("row-ingestion-skeleton-0")).toBeInTheDocument()
  })

  it("stops showing the skeleton once ingestion completes", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "completed",
      created_at: "2026-07-19T00:00:00Z",
    })

    render(<Harness status="uploaded" documentId="doc-1" />)

    await waitFor(() => expect(screen.getByText("Completed")).toBeInTheDocument())
    expect(screen.queryByTestId("row-ingestion-skeleton-0")).not.toBeInTheDocument()
  })

  it("shows Failed when the polled document no longer exists (404)", async () => {
    getDocumentStatusMock.mockRejectedValue(
      Object.assign(new Error("Not Found"), { isAxiosError: true, response: { status: 404 } })
    )

    render(<Harness status="uploaded" documentId="doc-gone" />)

    await waitFor(() => expect(screen.getByText("Failed")).toBeInTheDocument())
    expect(screen.queryByTestId("row-ingestion-skeleton-0")).not.toBeInTheDocument()
  })
})

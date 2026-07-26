import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const uploadDocumentMock = vi.fn()
const getDocumentStatusMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  uploadDocument: (...args: unknown[]) => uploadDocumentMock(...args),
  getDocumentStatus: (...args: unknown[]) => getDocumentStatusMock(...args),
}))

const MOCK_CLIENT = { id: "11111111-1111-1111-1111-111111111111", name: "Acme Staffing" }
const listClientsMock = vi.fn()
const createClientMock = vi.fn()
vi.mock("@/lib/api/clients", () => ({
  listClients: (...args: unknown[]) => listClientsMock(...args),
  createClient: (...args: unknown[]) => createClientMock(...args),
}))

import DocStudioPage from "./page"

function makeFile(name: string, size = 1024): File {
  const blob = new Blob([new Array(size).fill("a").join("")], {
    type: "application/pdf",
  })
  return new File([blob], name, { type: "application/pdf" })
}

function setFiles(input: HTMLElement, files: File[]) {
  Object.defineProperty(input, "files", {
    value: files,
    configurable: true,
    writable: true,
  })
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <DocStudioPage />
    </QueryClientProvider>
  )
}

/** Renders the page and waits for the client list to finish loading. */
async function renderWithClientLoaded() {
  renderPage()
  await waitFor(() => {
    expect(screen.getByTestId("client-select-input")).toHaveValue(MOCK_CLIENT.id)
  })
}

describe("Doc Studio upload page", () => {
  beforeEach(() => {
    uploadDocumentMock.mockReset()
    getDocumentStatusMock.mockReset()
    listClientsMock.mockReset()
    createClientMock.mockReset()
    listClientsMock.mockResolvedValue([MOCK_CLIENT])
  })

  it("renders the empty state when no files are queued", async () => {
    await renderWithClientLoaded()
    expect(screen.getByText("Document Upload")).toBeInTheDocument()
    expect(screen.getByTestId("queue-empty-state")).toBeInTheDocument()
  })

  it("adds a file to the queue with the filename as the default title", async () => {
    await renderWithClientLoaded()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)

    expect(screen.getByText("resume.pdf")).toBeInTheDocument()
    expect(screen.getByTestId("row-title-0")).toHaveValue("resume")
    expect(screen.getByTestId("submit-upload")).toBeEnabled()
  })

  it("uploads a queued file, captures its document id, and starts polling ingestion status", async () => {
    uploadDocumentMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      file_name: "resume.pdf",
      file_size_kb: 1,
      status: "uploaded",
      created_at: new Date().toISOString(),
    })
    getDocumentStatusMock.mockResolvedValue({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "extracting",
      created_at: new Date().toISOString(),
    })

    await renderWithClientLoaded()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)

    fireEvent.click(screen.getByTestId("submit-upload"))

    await waitFor(() => {
      expect(uploadDocumentMock).toHaveBeenCalledTimes(1)
    })
    const args = uploadDocumentMock.mock.calls[0]
    expect(args[1]).toMatchObject({
      title: "resume",
      doc_type: "other",
      client_id: MOCK_CLIENT.id,
    })

    // Row stays in the queue and starts polling the real ingestion status
    // instead of being removed once the upload HTTP call succeeds.
    await waitFor(() => {
      expect(getDocumentStatusMock).toHaveBeenCalledWith("doc-1")
    })
    await waitFor(() => {
      expect(screen.getByText("Extracting")).toBeInTheDocument()
    })
    expect(screen.getByText("resume.pdf")).toBeInTheDocument()
  })

  it("shows the completed badge and stops polling once ingestion finishes", async () => {
    uploadDocumentMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      file_name: "resume.pdf",
      file_size_kb: 1,
      status: "uploaded",
      created_at: new Date().toISOString(),
    })
    getDocumentStatusMock.mockResolvedValue({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "completed",
      created_at: new Date().toISOString(),
    })

    await renderWithClientLoaded()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)
    fireEvent.click(screen.getByTestId("submit-upload"))

    await waitFor(() => {
      expect(screen.getByText("Completed")).toBeInTheDocument()
    })
    expect(screen.queryByTestId("row-ingestion-skeleton-0")).not.toBeInTheDocument()
  })

  it("keeps the file in the queue and marks it failed on upload error", async () => {
    uploadDocumentMock.mockRejectedValueOnce(new Error("Network error"))

    await renderWithClientLoaded()
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)

    fireEvent.click(screen.getByTestId("submit-upload"))

    await waitFor(() => {
      expect(uploadDocumentMock).toHaveBeenCalledTimes(1)
    })
    await waitFor(() => {
      expect(screen.getByText("Failed")).toBeInTheDocument()
    })
    // File remains in the queue (failed -> visible row).
    expect(screen.getByText("resume.pdf")).toBeInTheDocument()
    expect(getDocumentStatusMock).not.toHaveBeenCalled()
  })

  it("shows an inline create-client form when no clients exist yet, and lets one be created", async () => {
    listClientsMock.mockResolvedValue([])
    const created = { id: "22222222-2222-2222-2222-222222222222", name: "New Co" }
    createClientMock.mockResolvedValueOnce(created)

    renderPage()
    await waitFor(() => {
      expect(listClientsMock).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByTestId("new-client-name")).toBeInTheDocument()
    fireEvent.change(screen.getByTestId("new-client-name"), {
      target: { value: "New Co" },
    })
    fireEvent.click(screen.getByText("Create"))

    await waitFor(() => {
      expect(createClientMock).toHaveBeenCalledWith({ name: "New Co" })
    })
    await waitFor(() => {
      expect(screen.getByTestId("client-select-input")).toHaveValue(created.id)
    })
  })

  it("does not queue files until a client is selected", async () => {
    listClientsMock.mockResolvedValue([])
    renderPage()
    await waitFor(() => {
      expect(listClientsMock).toHaveBeenCalledTimes(1)
    })

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)

    expect(screen.getByTestId("queue-empty-state")).toBeInTheDocument()
  })
})

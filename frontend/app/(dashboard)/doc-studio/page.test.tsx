import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"

const uploadDocumentMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  uploadDocument: (...args: unknown[]) => uploadDocumentMock(...args),
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

describe("Doc Studio upload page", () => {
  beforeEach(() => {
    uploadDocumentMock.mockReset()
  })

  it("renders the empty state when no files are queued", () => {
    render(<DocStudioPage />)
    expect(screen.getByText("Document Upload")).toBeInTheDocument()
    expect(screen.getByTestId("queue-empty-state")).toBeInTheDocument()
  })

  it("adds a file to the queue with the filename as the default title", () => {
    render(<DocStudioPage />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    setFiles(input, [makeFile("resume.pdf")])
    fireEvent.change(input)

    expect(screen.getByText("resume.pdf")).toBeInTheDocument()
    expect(screen.getByTestId("row-title-0")).toHaveValue("resume")
    expect(screen.getByTestId("submit-upload")).toBeEnabled()
  })

  it("uploads a queued file and removes it from the queue on success", async () => {
    uploadDocumentMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      file_name: "resume.pdf",
      file_size_kb: 1,
      status: "processing",
      created_at: new Date().toISOString(),
    })

    render(<DocStudioPage />)
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
      client_id: "default",
    })

    await waitFor(() => {
      expect(screen.getByTestId("queue-empty-state")).toBeInTheDocument()
    })
  })

  it("keeps the file in the queue and marks it failed on upload error", async () => {
    uploadDocumentMock.mockRejectedValueOnce(new Error("Network error"))

    render(<DocStudioPage />)
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
  })
})

import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"
import { FileDropzone } from "./file-dropzone"

function makeFile(name: string, size: number, type: string): File {
  // Uint8Array avoids the string-join allocation, which was slow enough on
  // 20+ MB files to make this test flaky against the 5000ms default timeout.
  return new File([new Uint8Array(size)], name, { type })
}

function setFiles(input: HTMLElement, files: File[]) {
  Object.defineProperty(input, "files", {
    value: files,
    configurable: true,
    writable: true,
  })
}

describe("FileDropzone", () => {
  let onFilesSelected: ReturnType<typeof vi.fn>

  beforeEach(() => {
    onFilesSelected = vi.fn()
  })

  it("accepts a valid PDF under the size limit", () => {
    render(<FileDropzone onFilesSelected={onFilesSelected} currentCount={0} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const pdf = makeFile("resume.pdf", 1024, "application/pdf")
    setFiles(input, [pdf])
    fireEvent.change(input)
    expect(onFilesSelected).toHaveBeenCalledWith([pdf])
  })

  it("accepts a DOCX file", () => {
    render(<FileDropzone onFilesSelected={onFilesSelected} currentCount={0} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const docx = makeFile(
      "offer.docx",
      1024,
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    setFiles(input, [docx])
    fireEvent.change(input)
    expect(onFilesSelected).toHaveBeenCalledWith([docx])
  })

  it("rejects unsupported file types", () => {
    render(<FileDropzone onFilesSelected={onFilesSelected} currentCount={0} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const txt = makeFile("notes.txt", 1024, "text/plain")
    setFiles(input, [txt])
    fireEvent.change(input)
    expect(onFilesSelected).toHaveBeenCalledWith([])
  })

  it("rejects files larger than 20 MB", () => {
    render(<FileDropzone onFilesSelected={onFilesSelected} currentCount={0} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const big = makeFile("big.pdf", 21 * 1024 * 1024, "application/pdf")
    setFiles(input, [big])
    fireEvent.change(input)
    expect(onFilesSelected).toHaveBeenCalledWith([])
  })

  it("respects the queue limit by dropping overflow files", () => {
    render(<FileDropzone onFilesSelected={onFilesSelected} currentCount={8} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const files = Array.from({ length: 5 }, (_, i) =>
      makeFile(`f${i}.pdf`, 1024, "application/pdf")
    )
    setFiles(input, files)
    fireEvent.change(input)
    // currentCount=8, MAX_QUEUE=10 -> only 2 more slots.
    expect(onFilesSelected).toHaveBeenCalledTimes(1)
    const passed = onFilesSelected.mock.calls[0][0] as File[]
    expect(passed).toHaveLength(2)
  })
})

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import type { DocumentDetail } from "@/types/api"
import {
  DocumentDetailView,
  ExtractedText,
  formatTimestamp,
  isIngesting,
  statusLabel,
} from "./document-detail-view"

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
    extracted_text: "First paragraph.\n\nSecond paragraph.",
    auto_tags: {
      document_type: "resume",
      candidate_name: "Priya Sharma",
      role: "Senior Backend Engineer",
      company: "Acme Corp",
      skills: ["Python", "FastAPI", "PostgreSQL"],
      date: "2026-05-01",
    },
    manual_tags: null,
    created_at: "2026-08-01T10:30:00Z",
    updated_at: "2026-08-01T10:32:00Z",
    deleted_at: null,
    ...overrides,
  }
}

describe("DocumentDetailView", () => {
  it("renders the document identity and status", () => {
    render(<DocumentDetailView document={makeDocument()} status="completed" />)

    expect(screen.getByText("Priya Sharma - Senior Backend Engineer")).toBeInTheDocument()
    expect(screen.getByText("priya-sharma.pdf")).toBeInTheDocument()
    expect(screen.getByTestId("detail-status")).toHaveTextContent("Completed")
  })

  it("maps the doc_type to its human label rather than the raw enum value", () => {
    render(<DocumentDetailView document={makeDocument()} status="completed" />)
    expect(screen.getByText("Resume")).toBeInTheDocument()
  })

  it("renders auto-tag fields and skills as chips", () => {
    render(<DocumentDetailView document={makeDocument()} status="completed" />)

    expect(screen.getByText("Priya Sharma")).toBeInTheDocument()
    expect(screen.getByText("Acme Corp")).toBeInTheDocument()
    const skills = screen.getByTestId("detail-skills")
    expect(skills).toHaveTextContent("Python")
    expect(skills).toHaveTextContent("FastAPI")
    expect(skills).toHaveTextContent("PostgreSQL")
  })

  it("falls back gracefully when auto-tagging produced nothing", () => {
    // A tagging failure persists an all-defaults AutoTags object rather
    // than failing the document, so this is a real state, not a hypothetical.
    render(
      <DocumentDetailView
        document={makeDocument({ auto_tags: null, manual_tags: null })}
        status="completed"
      />
    )

    expect(screen.getByText("No skills were extracted from this document.")).toBeInTheDocument()
    expect(screen.queryByTestId("detail-skills")).not.toBeInTheDocument()
    expect(screen.queryByTestId("detail-manual-tags")).not.toBeInTheDocument()
  })

  it("renders manual tags only when present", () => {
    render(
      <DocumentDetailView
        document={makeDocument({ manual_tags: ["shortlisted"] })}
        status="completed"
      />
    )
    expect(screen.getByTestId("detail-manual-tags")).toHaveTextContent("shortlisted")
  })

  it("shows an em dash for a missing file size rather than an empty cell", () => {
    render(
      <DocumentDetailView document={makeDocument({ file_size_kb: null })} status="completed" />
    )
    expect(screen.getAllByText("—").length).toBeGreaterThan(0)
  })

  it("prefers the passed-in status over the one on the cached record", () => {
    // The page polls /status separately, so a stale cached detail record
    // must not win over the freshly polled value.
    render(
      <DocumentDetailView document={makeDocument({ status: "extracting" })} status="completed" />
    )
    expect(screen.getByTestId("detail-status")).toHaveTextContent("Completed")
  })
})

describe("ExtractedText", () => {
  it("preserves paragraph breaks without parsing the content", () => {
    render(<ExtractedText text={"First paragraph.\n\nSecond paragraph."} status="completed" />)

    const body = screen.getByTestId("extracted-text")
    expect(body).toHaveTextContent("First paragraph.")
    expect(body).toHaveTextContent("Second paragraph.")
    expect(body.querySelector("p")).toHaveClass("whitespace-pre-wrap")
  })

  it("renders markup in the document as text, never as HTML", () => {
    // Extracted text is user-uploaded resume content. RF-107 may also
    // return ts_headline markup in a related field. Either way it must be
    // displayed, not interpreted.
    const hostile = "<script>window.__pwned = true</script><b>bold</b>"
    render(<ExtractedText text={hostile} status="completed" />)

    const body = screen.getByTestId("extracted-text")
    expect(body.querySelector("script")).toBeNull()
    expect(body.querySelector("b")).toBeNull()
    expect(body).toHaveTextContent("<script>window.__pwned = true</script><b>bold</b>")
  })

  it("shows the ingestion stage instead of an empty area while still processing", () => {
    render(<ExtractedText text={null} status="chunking" />)

    const pending = screen.getByTestId("extracted-text-pending")
    expect(pending).toHaveTextContent("Chunking")
    expect(screen.queryByTestId("extracted-text-empty")).not.toBeInTheDocument()
  })

  it("explains a failed ingestion rather than claiming the document is empty", () => {
    render(<ExtractedText text={null} status="failed" />)
    expect(screen.getByTestId("extracted-text-failed")).toBeInTheDocument()
  })

  it("reports a genuinely empty extraction on a completed document", () => {
    render(<ExtractedText text={null} status="completed" />)
    expect(screen.getByTestId("extracted-text-empty")).toBeInTheDocument()
  })

  it("shows the text once it exists even if the status is still in flight", () => {
    // Extraction is the first ingestion stage, so text is available well
    // before the document reaches "completed".
    render(<ExtractedText text="Already extracted." status="embedding" />)
    expect(screen.getByTestId("extracted-text")).toHaveTextContent("Already extracted.")
  })
})

describe("statusLabel / isIngesting", () => {
  it("labels every known backend ingestion status", () => {
    expect(statusLabel("uploaded")).toBe("Uploaded")
    expect(statusLabel("extracting")).toBe("Extracting text")
    expect(statusLabel("chunking")).toBe("Chunking")
    expect(statusLabel("embedding")).toBe("Embedding")
    expect(statusLabel("completed")).toBe("Completed")
    expect(statusLabel("failed")).toBe("Failed")
  })

  it("passes an unrecognized status through instead of rendering blank", () => {
    expect(statusLabel("some_new_stage")).toBe("some_new_stage")
  })

  it("treats only the in-flight stages as ingesting", () => {
    expect(isIngesting("extracting")).toBe(true)
    expect(isIngesting("embedding")).toBe(true)
    expect(isIngesting("completed")).toBe(false)
    expect(isIngesting("failed")).toBe(false)
  })
})

describe("formatTimestamp", () => {
  it("formats a valid ISO timestamp", () => {
    expect(formatTimestamp("2026-08-01T10:30:00Z")).toContain("2026")
  })

  it("returns the raw value when the timestamp will not parse", () => {
    expect(formatTimestamp("not-a-date")).toBe("not-a-date")
  })
})

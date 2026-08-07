"use client"

import * as React from "react"
import { FileText, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DOC_TYPE_VALUES, type DocumentDetail } from "@/types/api"

/**
 * Backend ingestion statuses, as persisted on the document row.
 *
 * Deliberately not shared with doc-studio's STAGE_LABELS: that union also
 * carries "queued" and "uploading", which are client-side upload-queue
 * states that exist only before a document id does and can therefore never
 * reach this view. Merging the two would mean rendering states this screen
 * cannot be in.
 */
const STATUS_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  extracting: "Extracting text",
  chunking: "Chunking",
  embedding: "Embedding",
  completed: "Completed",
  failed: "Failed",
}

const IN_FLIGHT_STATUSES = new Set(["uploaded", "extracting", "chunking", "embedding"])

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

export function isIngesting(status: string): boolean {
  return IN_FLIGHT_STATUSES.has(status)
}

function statusVariant(status: string): "success" | "destructive" | "secondary" {
  if (status === "completed") return "success"
  if (status === "failed") return "destructive"
  return "secondary"
}

function docTypeLabel(value: string): string {
  return DOC_TYPE_VALUES.find((d) => d.value === value)?.label ?? value
}

/** Renders an ISO timestamp, falling back to the raw string if it won't parse. */
export function formatTimestamp(iso: string): string {
  const parsed = new Date(iso)
  if (Number.isNaN(parsed.getTime())) return iso
  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function MetaField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value}</dd>
    </div>
  )
}

/**
 * Body of the document detail screen.
 *
 * Split out from page.tsx so it can be exercised on fixture data with no
 * live backend, no router, and no query client.
 *
 * `status` is passed in rather than read off `document.status` so the page
 * can supply the freshly-polled value while the cached detail record still
 * carries the status from whenever it was fetched.
 */
export function DocumentDetailView({
  document,
  status,
}: {
  document: DocumentDetail
  status: string
}) {
  const tags = document.auto_tags ?? {}
  const skills = tags.skills ?? []
  const manualTags = document.manual_tags ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 space-y-1">
          <h1 className="truncate text-2xl font-semibold" title={document.title}>
            {document.title}
          </h1>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4 shrink-0" />
            <span className="truncate" title={document.file_name}>
              {document.file_name}
            </span>
          </div>
        </div>
        <Badge
          variant={statusVariant(status)}
          aria-label={`Status: ${statusLabel(status)}`}
          data-testid="detail-status"
        >
          {statusLabel(status)}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetaField label="Type" value={docTypeLabel(document.doc_type)} />
            <MetaField
              label="Size"
              value={document.file_size_kb != null ? `${document.file_size_kb} KB` : "—"}
            />
            <MetaField label="Uploaded" value={formatTimestamp(document.created_at)} />
            <MetaField label="Updated" value={formatTimestamp(document.updated_at)} />
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Auto-tags</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetaField label="Candidate" value={tags.candidate_name || "—"} />
            <MetaField label="Role" value={tags.role || "—"} />
            <MetaField label="Company" value={tags.company || "—"} />
            <MetaField label="Date" value={tags.date || "—"} />
          </dl>

          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Skills</p>
            {skills.length > 0 ? (
              <div className="flex flex-wrap gap-2" data-testid="detail-skills">
                {skills.map((skill) => (
                  <Badge key={skill} variant="outline">
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No skills were extracted from this document.
              </p>
            )}
          </div>

          {manualTags.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Manual tags</p>
              <div className="flex flex-wrap gap-2" data-testid="detail-manual-tags">
                {manualTags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Extracted text</CardTitle>
        </CardHeader>
        <CardContent>
          <ExtractedText text={document.extracted_text} status={status} />
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * The extracted text is user-uploaded document content. It is rendered as
 * text - never as HTML - so a resume containing markup or a prompt-injection
 * payload is displayed, not executed. `whitespace-pre-wrap` preserves the
 * paragraph and line breaks the extractor produced without needing any
 * parsing of the content itself.
 */
export function ExtractedText({ text, status }: { text: string | null; status: string }) {
  if (text) {
    return (
      <div
        className="max-h-[60vh] overflow-y-auto rounded-md border border-border bg-muted/30 p-4"
        data-testid="extracted-text"
      >
        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{text}</p>
      </div>
    )
  }

  if (isIngesting(status)) {
    return (
      <div
        className="flex items-center gap-2 text-sm text-muted-foreground"
        data-testid="extracted-text-pending"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{statusLabel(status)} - the text will appear here once processing finishes.</span>
      </div>
    )
  }

  if (status === "failed") {
    return (
      <p className="text-sm text-muted-foreground" data-testid="extracted-text-failed">
        Processing failed for this document, so no text was extracted. Re-uploading it is usually
        the quickest fix.
      </p>
    )
  }

  return (
    <p className="text-sm text-muted-foreground" data-testid="extracted-text-empty">
      No text was extracted from this document.
    </p>
  )
}

export default DocumentDetailView

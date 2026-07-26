"use client"

import * as React from "react"
import { Controller, type Control, type UseFormRegister } from "react-hook-form"
import { X, FileText } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useDocumentStatusPolling, isNotFoundError } from "@/lib/hooks/use-document-status"
import { DOC_TYPE_OPTIONS, type QueueFormValues, type UploadStatus } from "../schema"

interface UploadMetadataRowProps {
  index: number
  control: Control<QueueFormValues>
  register: UseFormRegister<QueueFormValues>
  fileName: string
  status: UploadStatus
  documentId?: string
  error?: string
  onRemove: () => void
  disabled: boolean
}

const INGESTION_STAGES = new Set<UploadStatus>(["uploaded", "extracting", "chunking", "embedding"])

const STAGE_LABELS: Record<UploadStatus, string> = {
  queued: "Queued",
  uploading: "Uploading",
  uploaded: "Uploaded",
  extracting: "Extracting",
  chunking: "Chunking",
  embedding: "Embedding",
  completed: "Completed",
  failed: "Failed",
}

function statusBadge(status: UploadStatus) {
  const label = STAGE_LABELS[status]
  switch (status) {
    case "completed":
      return (
        <Badge variant="success" aria-label={`Status: ${label}`}>
          {label}
        </Badge>
      )
    case "failed":
      return (
        <Badge variant="destructive" aria-label={`Status: ${label}`}>
          {label}
        </Badge>
      )
    case "queued":
      return (
        <Badge variant="outline" aria-label={`Status: ${label}`}>
          {label}
        </Badge>
      )
    default:
      return (
        <Badge variant="secondary" aria-label={`Status: ${label}`}>
          {label}
        </Badge>
      )
  }
}

export function UploadMetadataRow({
  index,
  control,
  register,
  fileName,
  status: localStatus,
  documentId,
  error,
  onRemove,
  disabled,
}: UploadMetadataRowProps) {
  const polled = useDocumentStatusPolling(documentId)
  // Once a document id exists the upload HTTP call already succeeded -
  // display the real backend ingestion stage instead of the local status,
  // falling back to "uploaded" until the first poll resolves. A 404 means
  // the document is gone server-side; treat that as a terminal failure.
  const status: UploadStatus = documentId
    ? isNotFoundError(polled.error)
      ? "failed"
      : ((polled.data?.status as UploadStatus | undefined) ?? "uploaded")
    : localStatus

  return (
    <div
      className="rounded-md border border-border bg-card p-4"
      data-testid={`metadata-row-${index}`}
    >
      <div className="flex items-start justify-between gap-3 pb-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span
            className="truncate text-sm font-medium"
            title={fileName}
            data-testid={`row-filename-${index}`}
          >
            {fileName}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {statusBadge(status)}
          <button
            type="button"
            onClick={onRemove}
            disabled={disabled || status === "uploading"}
            className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
            aria-label={`Remove ${fileName} from queue`}
            data-testid={`row-remove-${index}`}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {INGESTION_STAGES.has(status) ? (
        <div
          className="mb-3 h-1.5 w-full animate-pulse rounded-full bg-muted"
          data-testid={`row-ingestion-skeleton-${index}`}
        />
      ) : null}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor={`items.${index}.title`}>Title</Label>
          <Input
            id={`items.${index}.title`}
            disabled={disabled || status === "uploading"}
            {...register(`items.${index}.title` as const)}
            data-testid={`row-title-${index}`}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor={`items.${index}.doc_type`}>Document Type</Label>
          <Controller
            control={control}
            name={`items.${index}.doc_type` as const}
            render={({ field }) => (
              <Select
                id={`items.${index}.doc_type`}
                disabled={disabled || status === "uploading"}
                aria-label="Document type"
                data-testid={`row-doctype-${index}`}
                value={field.value}
                onChange={(e) => field.onChange(e.target.value)}
                onBlur={field.onBlur}
              >
                {DOC_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            )}
          />
        </div>
      </div>

      {error ? (
        <p className="mt-2 text-xs text-red-400" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}

export default UploadMetadataRow

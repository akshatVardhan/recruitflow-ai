"use client"

import * as React from "react"
import { Controller, type Control, type UseFormRegister } from "react-hook-form"
import { X, FileText } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { DOC_TYPE_OPTIONS, type QueueFormValues, type UploadStatus } from "../schema"

interface UploadMetadataRowProps {
  index: number
  control: Control<QueueFormValues>
  register: UseFormRegister<QueueFormValues>
  fileName: string
  status: UploadStatus
  error?: string
  onRemove: () => void
  disabled: boolean
}

function statusBadge(status: UploadStatus) {
  switch (status) {
    case "uploading":
      return (
        <Badge variant="secondary" aria-label="Status: uploading">
          Uploading
        </Badge>
      )
    case "completed":
      return (
        <Badge variant="success" aria-label="Status: completed">
          Completed
        </Badge>
      )
    case "failed":
      return (
        <Badge variant="destructive" aria-label="Status: failed">
          Failed
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" aria-label="Status: queued">
          Queued
        </Badge>
      )
  }
}

export function UploadMetadataRow({
  index,
  control,
  register,
  fileName,
  status,
  error,
  onRemove,
  disabled,
}: UploadMetadataRowProps) {
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

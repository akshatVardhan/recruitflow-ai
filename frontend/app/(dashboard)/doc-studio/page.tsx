"use client"

import * as React from "react"
import { AxiosError } from "axios"
import { useFieldArray, useForm } from "react-hook-form"
import { Loader2, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "@/hooks/use-toast"
import { uploadDocument } from "@/lib/api/documents"
import { createClient, listClients } from "@/lib/api/clients"
import { zodResolver } from "@/lib/zod-resolver"
import type { Client } from "@/types/api"
import { ClientSelector } from "./components/client-selector"
import { FileDropzone } from "./components/file-dropzone"
import { UploadMetadataRow } from "./components/upload-metadata"
import { QueueEmptyState } from "./components/empty-state"
import { queueFormSchema, type QueueFormValues, type UploadStatus } from "./schema"

function stripExtension(name: string): string {
  const dot = name.lastIndexOf(".")
  return dot > 0 ? name.slice(0, dot) : name
}

function extractErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data as { detail?: unknown } | undefined
    if (typeof detail?.detail === "string") return detail.detail
    if (err.response?.status === 422) {
      return "The backend rejected the request (validation failed)."
    }
    if (err.code === "ERR_NETWORK") {
      return "Network error - could not reach the server."
    }
    return err.message
  }
  if (err instanceof Error) return err.message
  return "Unexpected error"
}

function firstRowError(
  // errors.items is a union of FieldError | nested FieldErrors; we only
  // need the human message, so read it loosely.
  errs: unknown,
  index: number
): string | undefined {
  const items = (errs as { items?: unknown } | undefined)?.items
  const row = (
    items as unknown as
      | Array<{
          title?: { message?: string }
          doc_type?: { message?: string }
          client_id?: { message?: string }
        }>
      | undefined
  )?.[index]
  return row?.title?.message ?? row?.doc_type?.message ?? row?.client_id?.message
}

export default function DocStudioPage() {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<QueueFormValues>({
    defaultValues: { items: [] },
    resolver: zodResolver(queueFormSchema),
  })
  const { fields, append, remove, replace } = useFieldArray({
    control,
    name: "items",
  })

  const [status, setStatus] = React.useState<Record<string, UploadStatus>>({})
  const [submitting, setSubmitting] = React.useState(false)

  const [clients, setClients] = React.useState<Client[]>([])
  const [clientsLoading, setClientsLoading] = React.useState(true)
  const [creatingClient, setCreatingClient] = React.useState(false)
  const [selectedClientId, setSelectedClientId] = React.useState<string | null>(null)

  React.useEffect(() => {
    let cancelled = false
    listClients()
      .then((data) => {
        if (cancelled) return
        setClients(data)
        if (data.length > 0) setSelectedClientId(data[0].id)
      })
      .catch(() => {
        if (!cancelled) {
          toast({
            variant: "destructive",
            title: "Could not load clients",
            description: "Check that you're signed in and try again.",
          })
        }
      })
      .finally(() => {
        if (!cancelled) setClientsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleCreateClient = React.useCallback(async (name: string) => {
    setCreatingClient(true)
    try {
      const client = await createClient({ name })
      setClients((prev) => [...prev, client])
      setSelectedClientId(client.id)
    } catch {
      toast({
        variant: "destructive",
        title: "Could not create client",
        description: "Please try again.",
      })
    } finally {
      setCreatingClient(false)
    }
  }, [])

  const handleFilesSelected = React.useCallback(
    (files: File[]) => {
      if (files.length === 0 || !selectedClientId) return
      append(
        files.map((file) => ({
          title: stripExtension(file.name),
          doc_type: "other" as const,
          client_id: selectedClientId,
          file,
        }))
      )
    },
    [append, selectedClientId]
  )

  const handleRemove = React.useCallback(
    (index: number, id: string) => {
      remove(index)
      setStatus((prev) => {
        const next = { ...prev }
        delete next[id]
        return next
      })
    },
    [remove]
  )

  const onSubmit = handleSubmit(async (values) => {
    const items = values.items ?? []
    if (items.length === 0 || fields.length === 0) return
    setSubmitting(true)
    let succeeded = 0
    let failed = 0
    const completedIndices: number[] = []

    for (let i = 0; i < fields.length; i++) {
      const fieldId = fields[i].id
      // Skip already completed rows (e.g. partial retry).
      if (status[fieldId] === "completed") continue
      const item = items[i]
      const file = item?.file
      if (!file) {
        setStatus((p) => ({ ...p, [fieldId]: "failed" }))
        failed++
        continue
      }
      setStatus((p) => ({ ...p, [fieldId]: "uploading" }))
      try {
        await uploadDocument(file, {
          title: item.title,
          doc_type: item.doc_type,
          client_id: item.client_id,
        })
        setStatus((p) => ({ ...p, [fieldId]: "completed" }))
        toast({
          variant: "success",
          title: "Document uploaded",
          description: `${item.title} uploaded successfully.`,
        })
        succeeded++
        completedIndices.push(i)
      } catch (err) {
        setStatus((p) => ({ ...p, [fieldId]: "failed" }))
        failed++
        toast({
          variant: "destructive",
          title: "Failed to upload document",
          description: `${item.title}: ${extractErrorMessage(err)}`,
          duration: 8000,
        })
      }
    }

    // Remove completed files from the queue (newest-settled first so
    // earlier indices remain valid during removal).
    completedIndices.sort((a, b) => b - a)
    for (const idx of completedIndices) {
      const fieldId = fields[idx].id
      remove(idx)
      setStatus((prev) => {
        const next = { ...prev }
        delete next[fieldId]
        return next
      })
    }

    setSubmitting(false)
    if (succeeded > 0 && failed > 0) {
      toast({
        variant: "info",
        title: "Completed with errors",
        description: `${succeeded} uploaded, ${failed} failed.`,
      })
    }
  })

  const inProgress = Object.values(status).some((s) => s === "uploading")
  const queueCount = fields.length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Document Upload</h1>
        <p className="text-sm text-muted-foreground">
          Upload reference documents for the RAG pipeline. Files are extracted, auto-tagged, and
          indexed automatically.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload files</CardTitle>
          <CardDescription>
            PDF or DOCX, up to 20 MB each. Up to 10 files per batch.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ClientSelector
            clients={clients}
            loading={clientsLoading}
            selectedId={selectedClientId}
            onSelect={setSelectedClientId}
            onCreate={handleCreateClient}
            creating={creatingClient}
          />

          <FileDropzone
            onFilesSelected={handleFilesSelected}
            currentCount={queueCount}
            disabled={submitting || inProgress || !selectedClientId}
          />

          {queueCount === 0 ? (
            <QueueEmptyState />
          ) : (
            <div className="space-y-3">
              {fields.map((field, index) => (
                <UploadMetadataRow
                  key={field.id}
                  index={index}
                  control={control}
                  register={register}
                  fileName={field.file?.name ?? "Untitled"}
                  status={status[field.id] ?? "queued"}
                  error={firstRowError(errors, index)}
                  onRemove={() => handleRemove(index, field.id)}
                  disabled={submitting}
                />
              ))}
            </div>
          )}

          {queueCount > 0 ? (
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  replace([])
                  setStatus({})
                }}
                disabled={submitting || inProgress}
                data-testid="clear-queue"
              >
                Clear
              </Button>
              <Button
                type="button"
                onClick={() => void onSubmit()}
                disabled={submitting || inProgress || queueCount === 0}
                data-testid="submit-upload"
              >
                {submitting || inProgress ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                {submitting || inProgress ? "Uploading..." : "Upload"}
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}

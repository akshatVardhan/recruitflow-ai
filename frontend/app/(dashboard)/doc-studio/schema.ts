import { z } from "zod"
import { DOC_TYPE_VALUES, type DocType } from "@/types/api"

export const docTypeValues = DOC_TYPE_VALUES.map((d) => d.value) as [DocType, ...DocType[]]

export const metadataItemSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or fewer"),
  doc_type: z.enum(docTypeValues),
  // Set programmatically from the selected client (see ClientSelector), not
  // user-edited - the backend requires a real client UUID (RF-CONTRACT-1).
  client_id: z.string().uuid("A client must be selected"),
  // File travels with each metadata row so it survives reorders / removes.
  // Not part of the validation contract.
  file: z.custom<File>().optional(),
})

export const queueFormSchema = z.object({
  items: z.array(metadataItemSchema),
})

export type MetadataItemValues = z.infer<typeof metadataItemSchema>
export type QueueFormValues = z.infer<typeof queueFormSchema>

export type UploadStatus = "queued" | "uploading" | "completed" | "failed"

export const DOC_TYPE_OPTIONS = DOC_TYPE_VALUES

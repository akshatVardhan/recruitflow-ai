import api from "@/lib/api"
import type { UploadMetadata, UploadResponse } from "@/types/api"

const UPLOAD_PATH = "/api/v1/documents/upload"

/**
 * Upload a single document to the backend ingestion pipeline.
 * Sends multipart/form-data with file + metadata form fields.
 * JWT Authorization header is added automatically by the api interceptor.
 */
export async function uploadDocument(
  file: File,
  metadata: UploadMetadata
): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("title", metadata.title)
  form.append("doc_type", metadata.doc_type)
  form.append("client_id", metadata.client_id)

  const { data } = await api.post<UploadResponse>(UPLOAD_PATH, form, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

# RF-29: Upload Progress and Ingestion Status UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Poll each uploaded document's real backend ingestion status in Doc Studio's upload queue and reflect it in the row UI, instead of marking a row "completed" the instant the upload HTTP call returns.

**Architecture:** Wire TanStack Query (installed, unused) into the app via a root `QueryClientProvider`. Add a `getDocumentStatus` API helper and a small `useDocumentStatusPolling` hook that polls `GET /api/v1/documents/{id}/status` every 2s while the backend status is non-terminal, and stops once `completed`/`failed`. Each queue row uses the hook directly once it has a captured document id; the parent page only needs to capture and pass that id through.

**Tech Stack:** Next.js (App Router), React 19, TanStack Query v5, react-hook-form + Zod, Vitest + Testing Library (existing stack, no new deps).

## Global Constraints

- No Lottie animation — not specified in `.claude/rules/design-system.md`, no asset/dependency in the repo (per design decision).
- Skeleton loaders (pulsing bar) for in-flight states, per `.claude/rules/design-system.md`'s "Skeleton Loaders" rule — never a spinner as the sole content-area loading indicator.
- Do not rely on color alone for status — always pair a badge with text (per `.claude/rules/design-system.md` Accessibility section).
- No new page — `/documents` list page stays a stub, out of scope.
- Poll interval: 2000ms while status is `uploaded | extracting | chunking | embedding`; stop (`false`) once `completed` or `failed`.
- Backend status values (exhaustive, from `backend/app/modules/documents/models.py:37`): `uploaded`, `extracting`, `chunking`, `embedding`, `completed`, `failed`.

---

### Task 1: TanStack Query provider + status API + polling hook

**Files:**
- Modify: `frontend/types/api.ts` (add `DocumentStatusResponse`)
- Modify: `frontend/lib/api/documents.ts` (add `getDocumentStatus`)
- Create: `frontend/app/query-provider.tsx`
- Modify: `frontend/app/layout.tsx` (mount the provider)
- Create: `frontend/lib/hooks/use-document-status.ts`
- Test: `frontend/lib/hooks/use-document-status.test.tsx`

**Interfaces:**
- Produces: `DocumentStatusResponse` type (`{ id: string; title: string; doc_type: string; status: string; created_at: string }`), `getDocumentStatus(id: string): Promise<DocumentStatusResponse>`, `nextPollInterval(status: string | undefined): number | false`, `isNotFoundError(error: unknown): boolean`, `useDocumentStatusPolling(documentId: string | undefined)` returning a TanStack Query `UseQueryResult<DocumentStatusResponse>`.

- [ ] **Step 1: Add the `DocumentStatusResponse` type**

Append to `frontend/types/api.ts` (after the existing `UploadResponse` interface, i.e. after line 80):

```ts
export interface DocumentStatusResponse {
  id: string
  title: string
  doc_type: string
  status: string
  created_at: string
}
```

- [ ] **Step 2: Add the `getDocumentStatus` API helper**

Replace the full contents of `frontend/lib/api/documents.ts` with:

```ts
import api from "@/lib/api"
import type { DocumentStatusResponse, UploadMetadata, UploadResponse } from "@/types/api"

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

/** Fetches the current ingestion status for a previously uploaded document. */
export async function getDocumentStatus(id: string): Promise<DocumentStatusResponse> {
  const { data } = await api.get<DocumentStatusResponse>(`/api/v1/documents/${id}/status`)
  return data
}
```

- [ ] **Step 3: Add the QueryClientProvider wrapper and mount it in the root layout**

Create `frontend/app/query-provider.tsx`:

```tsx
"use client"

import * as React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(() => new QueryClient())
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
```

Replace the full contents of `frontend/app/layout.tsx` with:

```tsx
import type { Metadata } from "next"
import "./globals.css"
import { QueryProvider } from "./query-provider"

export const metadata: Metadata = {
  title: "RecruitFlow AI",
  description: "AI-powered recruitment platform",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
```

- [ ] **Step 4: Write the failing test for the polling hook**

Create `frontend/lib/hooks/use-document-status.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

const getDocumentStatusMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  getDocumentStatus: (...args: unknown[]) => getDocumentStatusMock(...args),
}))

import { useDocumentStatusPolling, nextPollInterval, isNotFoundError } from "./use-document-status"

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe("nextPollInterval", () => {
  it("returns the polling interval for in-flight statuses", () => {
    expect(nextPollInterval("uploaded")).toBe(2000)
    expect(nextPollInterval("extracting")).toBe(2000)
    expect(nextPollInterval("chunking")).toBe(2000)
    expect(nextPollInterval("embedding")).toBe(2000)
    expect(nextPollInterval(undefined)).toBe(2000)
  })

  it("returns false for terminal statuses", () => {
    expect(nextPollInterval("completed")).toBe(false)
    expect(nextPollInterval("failed")).toBe(false)
  })
})

describe("useDocumentStatusPolling", () => {
  beforeEach(() => {
    getDocumentStatusMock.mockReset()
  })

  it("does not fetch when no documentId is given", () => {
    const { result } = renderHook(() => useDocumentStatusPolling(undefined), { wrapper })
    expect(getDocumentStatusMock).not.toHaveBeenCalled()
    expect(result.current.data).toBeUndefined()
  })

  it("fetches status once a documentId is given", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "extracting",
      created_at: "2026-07-19T00:00:00Z",
    })

    const { result } = renderHook(() => useDocumentStatusPolling("doc-1"), { wrapper })

    await waitFor(() => expect(result.current.data?.status).toBe("extracting"))
    expect(getDocumentStatusMock).toHaveBeenCalledWith("doc-1")
  })

  it("does not retry a 404 - the document is gone, so one failed fetch is terminal", async () => {
    getDocumentStatusMock.mockRejectedValue(
      Object.assign(new Error("Not Found"), { isAxiosError: true, response: { status: 404 } })
    )

    const { result } = renderHook(() => useDocumentStatusPolling("doc-missing"), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))
    // Give any (incorrect) retry a tick to fire before asserting call count.
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(getDocumentStatusMock).toHaveBeenCalledTimes(1)
  })
})

describe("isNotFoundError", () => {
  it("recognizes a 404 axios error", () => {
    const err = Object.assign(new Error("Not Found"), {
      isAxiosError: true,
      response: { status: 404 },
    })
    expect(isNotFoundError(err)).toBe(true)
  })

  it("returns false for other errors", () => {
    expect(isNotFoundError(new Error("boom"))).toBe(false)
    expect(
      isNotFoundError(
        Object.assign(new Error("Server Error"), { isAxiosError: true, response: { status: 500 } })
      )
    ).toBe(false)
  })
})
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `cd frontend && npx vitest run lib/hooks/use-document-status.test.tsx`
Expected: FAIL with a module-not-found error for `./use-document-status` (the hook doesn't exist yet).

- [ ] **Step 6: Implement the polling hook**

Create `frontend/lib/hooks/use-document-status.ts`:

```ts
"use client"

import { isAxiosError } from "axios"
import { useQuery } from "@tanstack/react-query"
import { getDocumentStatus } from "@/lib/api/documents"

const POLLING_INTERVAL_MS = 2000
const TERMINAL_STATUSES = new Set(["completed", "failed"])

/** Poll interval for a document's ingestion status: 2s while in-flight, stop once terminal. */
export function nextPollInterval(status: string | undefined): number | false {
  return TERMINAL_STATUSES.has(status ?? "") ? false : POLLING_INTERVAL_MS
}

/** A 404 means the document is gone - treat it as a terminal failure, never retry or re-poll it. */
export function isNotFoundError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 404
}

export function useDocumentStatusPolling(documentId: string | undefined) {
  return useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => getDocumentStatus(documentId as string),
    enabled: !!documentId,
    retry: (failureCount, error) => !isNotFoundError(error) && failureCount < 3,
    refetchInterval: (query) =>
      isNotFoundError(query.state.error) ? false : nextPollInterval(query.state.data?.status),
  })
}
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd frontend && npx vitest run lib/hooks/use-document-status.test.tsx`
Expected: PASS (7 tests)

- [ ] **Step 8: Commit**

```bash
git add frontend/types/api.ts frontend/lib/api/documents.ts frontend/app/query-provider.tsx frontend/app/layout.tsx frontend/lib/hooks/use-document-status.ts frontend/lib/hooks/use-document-status.test.tsx
git commit -m "feat: wire TanStack Query + document status polling hook RF-29"
```

---

### Task 2: Extend `UploadStatus` and render ingestion stages in the row

**Files:**
- Modify: `frontend/app/(dashboard)/doc-studio/schema.ts` (extend `UploadStatus`)
- Modify: `frontend/app/(dashboard)/doc-studio/components/upload-metadata.tsx` (accept `documentId`, poll, render stage badge + skeleton)
- Test: `frontend/app/(dashboard)/doc-studio/components/upload-metadata.test.tsx`

**Interfaces:**
- Consumes: `useDocumentStatusPolling` and `isNotFoundError` from Task 1 (`frontend/lib/hooks/use-document-status.ts`).
- Produces: `UploadStatus` now includes the 4 backend in-flight stages; `UploadMetadataRow` accepts an optional `documentId?: string` prop.

- [ ] **Step 1: Extend the `UploadStatus` type**

In `frontend/app/(dashboard)/doc-studio/schema.ts`, replace line 30:

```ts
export type UploadStatus = "queued" | "uploading" | "completed" | "failed"
```

with:

```ts
export type UploadStatus =
  | "queued"
  | "uploading"
  | "uploaded"
  | "extracting"
  | "chunking"
  | "embedding"
  | "completed"
  | "failed"
```

- [ ] **Step 2: Write the failing test for the row's ingestion display**

Create `frontend/app/(dashboard)/doc-studio/components/upload-metadata.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { useForm } from "react-hook-form"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { UploadMetadataRow } from "./upload-metadata"
import type { QueueFormValues, UploadStatus } from "../schema"

const getDocumentStatusMock = vi.fn()
vi.mock("@/lib/api/documents", () => ({
  getDocumentStatus: (...args: unknown[]) => getDocumentStatusMock(...args),
}))

function Harness({ status, documentId }: { status: UploadStatus; documentId?: string }) {
  const { control, register } = useForm<QueueFormValues>({
    defaultValues: {
      items: [
        { title: "resume", doc_type: "other", client_id: "11111111-1111-1111-1111-111111111111" },
      ],
    },
  })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <UploadMetadataRow
        index={0}
        control={control}
        register={register}
        fileName="resume.pdf"
        status={status}
        documentId={documentId}
        onRemove={() => {}}
        disabled={false}
      />
    </QueryClientProvider>
  )
}

describe("UploadMetadataRow ingestion status", () => {
  beforeEach(() => {
    getDocumentStatusMock.mockReset()
  })

  it("shows the local upload status when no documentId is set yet", () => {
    render(<Harness status="uploading" />)
    expect(screen.getByText("Uploading")).toBeInTheDocument()
    expect(getDocumentStatusMock).not.toHaveBeenCalled()
  })

  it("polls and shows the backend ingestion stage once a documentId is set", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "extracting",
      created_at: "2026-07-19T00:00:00Z",
    })

    render(<Harness status="uploaded" documentId="doc-1" />)

    await waitFor(() => expect(screen.getByText("Extracting")).toBeInTheDocument())
    expect(screen.getByTestId("row-ingestion-skeleton-0")).toBeInTheDocument()
  })

  it("stops showing the skeleton once ingestion completes", async () => {
    getDocumentStatusMock.mockResolvedValueOnce({
      id: "doc-1",
      title: "resume",
      doc_type: "resume",
      status: "completed",
      created_at: "2026-07-19T00:00:00Z",
    })

    render(<Harness status="uploaded" documentId="doc-1" />)

    await waitFor(() => expect(screen.getByText("Completed")).toBeInTheDocument())
    expect(screen.queryByTestId("row-ingestion-skeleton-0")).not.toBeInTheDocument()
  })

  it("shows Failed when the polled document no longer exists (404)", async () => {
    getDocumentStatusMock.mockRejectedValue(
      Object.assign(new Error("Not Found"), { isAxiosError: true, response: { status: 404 } })
    )

    render(<Harness status="uploaded" documentId="doc-gone" />)

    await waitFor(() => expect(screen.getByText("Failed")).toBeInTheDocument())
    expect(screen.queryByTestId("row-ingestion-skeleton-0")).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd frontend && npx vitest run app/\(dashboard\)/doc-studio/components/upload-metadata.test.tsx`
Expected: FAIL - `documentId` prop doesn't exist / "Extracting" text not found (component doesn't poll yet).

- [ ] **Step 4: Implement the row changes**

Replace the full contents of `frontend/app/(dashboard)/doc-studio/components/upload-metadata.tsx` with:

```tsx
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd frontend && npx vitest run app/\(dashboard\)/doc-studio/components/upload-metadata.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add frontend/app/\(dashboard\)/doc-studio/schema.ts frontend/app/\(dashboard\)/doc-studio/components/upload-metadata.tsx frontend/app/\(dashboard\)/doc-studio/components/upload-metadata.test.tsx
git commit -m "feat: render backend ingestion stage with skeleton loader per row RF-29"
```

---

### Task 3: Capture document id in the queue and stop auto-removing uploaded rows

**Files:**
- Modify: `frontend/app/(dashboard)/doc-studio/page.tsx`
- Modify: `frontend/app/(dashboard)/doc-studio/page.test.tsx`

**Interfaces:**
- Consumes: `UploadMetadataRow`'s new `documentId?: string` prop (Task 2); `getDocumentStatus` mock contract (Task 1/2).
- Produces: none (top of the tree for this feature).

- [ ] **Step 1: Update the failing/changed tests first**

Replace the full contents of `frontend/app/(dashboard)/doc-studio/page.test.tsx` with:

```tsx
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && npx vitest run "app/(dashboard)/doc-studio/page.test.tsx"`
Expected: FAIL - the "captures its document id" and "shows the completed badge" tests fail because `page.tsx` still discards the id and removes the row on upload success.

- [ ] **Step 3: Implement the page changes**

Replace the full contents of `frontend/app/(dashboard)/doc-studio/page.tsx` with:

```tsx
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

export function extractErrorMessage(err: unknown): string {
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
          file?: { message?: string }
        }>
      | undefined
  )?.[index]
  return (
    row?.title?.message ?? row?.doc_type?.message ?? row?.client_id?.message ?? row?.file?.message
  )
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
  // Maps field id -> backend document id, captured once the upload POST
  // succeeds, so each row can poll its own ingestion status (RF-29).
  const [documentIds, setDocumentIds] = React.useState<Record<string, string>>({})
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
      setDocumentIds((prev) => {
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

    for (let i = 0; i < fields.length; i++) {
      const fieldId = fields[i].id
      // Skip rows that already uploaded successfully (queued/failed rows
      // are retried; anything past "uploading" has a document id and is
      // tracked by its own status poll instead).
      if (status[fieldId] && status[fieldId] !== "failed") continue
      const item = items[i]
      const file = item?.file
      if (!file) {
        setStatus((p) => ({ ...p, [fieldId]: "failed" }))
        failed++
        continue
      }
      setStatus((p) => ({ ...p, [fieldId]: "uploading" }))
      try {
        const document = await uploadDocument(file, {
          title: item.title,
          doc_type: item.doc_type,
          client_id: item.client_id,
        })
        setStatus((p) => ({ ...p, [fieldId]: "uploaded" }))
        setDocumentIds((p) => ({ ...p, [fieldId]: document.id }))
        toast({
          variant: "success",
          title: "Document uploaded",
          description: `${item.title} uploaded successfully. Processing...`,
        })
        succeeded++
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
                  documentId={documentIds[field.id]}
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
                  setDocumentIds({})
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && npx vitest run "app/(dashboard)/doc-studio/page.test.tsx"`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/app/\(dashboard\)/doc-studio/page.tsx frontend/app/\(dashboard\)/doc-studio/page.test.tsx
git commit -m "feat: capture document id and poll ingestion status in upload queue RF-29"
```

---

### Task 4: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: PASS, no regressions in unrelated suites (`file-dropzone.test.tsx`, `layout.test.tsx`, etc.)

- [ ] **Step 2: Type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Manual smoke check in the dev server**

Run: `cd frontend && npm run dev`, open `/doc-studio`, select/create a client, queue a PDF, click Upload. Confirm the row stays visible post-upload showing a skeleton + stage label ("Uploaded"/"Extracting"/etc.) if a local backend is reachable at `NEXT_PUBLIC_API_BASE_URL`, or confirm the row at minimum renders without runtime errors and shows the "Uploaded" fallback state if no backend is reachable (network error is expected and acceptable here - this step is a rendering smoke check, not an end-to-end ingestion check).

- [ ] **Step 4: Commit any fixups only if step 1-3 surfaced issues**

(No commit if everything already passed in Task 1-3 commits.)

# RF-29: Upload Progress and Ingestion Status UI

## Problem

Doc Studio's upload queue (`frontend/app/(dashboard)/doc-studio/page.tsx`) tracks
each file with a local `queued | uploading | completed | failed` status, but that
status only reflects the HTTP upload call. Once the upload POST succeeds, the row
is marked `completed` and the returned document `id` is discarded — there's no
visibility into the actual backend ingestion pipeline (`uploaded -> extracting ->
chunking -> embedding -> completed/failed`), which runs asynchronously after the
upload responds.

## Scope

Extend the existing Doc Studio upload queue to poll each uploaded document's real
ingestion status and reflect it in the row UI. No new page — the `/documents`
list page stays a stub (out of scope). No Lottie animation: `design-system.md`
does not specify one and no asset/dependency exists in the repo; the skeleton-
loader rule it does specify covers the loading states.

## Design

**TanStack Query wiring** (first consumer in this repo)
- Add a `"use client"` `QueryProvider` wrapper around a `QueryClient` instance,
  mounted in `frontend/app/layout.tsx`.

**API helper**
- Add `getDocumentStatus(id: string): Promise<DocumentStatusResponse>` to
  `frontend/lib/api/documents.ts`, calling `GET /api/v1/documents/{id}/status`.

**Doc Studio queue changes**
- Capture `id` from the `UploadResponse` on successful upload instead of
  discarding it; keep the row in the queue (don't clear it post-upload).
- Each row with a captured `id` runs a `useQuery` keyed on that id, with
  `refetchInterval: 2000` while `status` is one of
  `uploaded | extracting | chunking | embedding`, and `refetchInterval: false`
  once `completed` or `failed`.
- Row status text/badge maps 1:1 to the backend's status string — no synthetic
  progress percentage, since the API doesn't expose one.

**Visual states** (per `design-system.md`'s skeleton-loader rule; no spinner-only
states, no color-alone status)
- In-flight (`uploaded`/`extracting`/`chunking`/`embedding`): pulsing skeleton
  bar + the stage name as text.
- `completed`: green-500 success icon + "Completed" text. Terminal, stops
  polling.
- `failed`: red-500 error icon + "Failed" text. Terminal, stops polling. The
  status endpoint has no error-message field, so no richer detail is shown.

**Error handling**
- Transient network/5xx errors on a status poll: TanStack Query's default
  retry/backoff applies; the row keeps showing its last-known state rather than
  flashing an error.
- 404 (document not found): treated as a terminal `failed` state for that row.

## Testing

One component test for the polling row: mock `getDocumentStatus` to return a
status sequence, assert the row transitions through the stages and stops
polling at a terminal state. No e2e or Lottie-specific testing (no Lottie in
this design).

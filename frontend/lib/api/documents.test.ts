import { describe, it, expect, vi, beforeEach } from "vitest"

const postMock = vi.fn()
vi.mock("@/lib/api", () => ({
  default: { post: (...args: unknown[]) => postMock(...args) },
}))

import { uploadDocument } from "./documents"

describe("uploadDocument", () => {
  beforeEach(() => {
    postMock.mockReset()
  })

  it("posts multipart form data with file and metadata fields", async () => {
    postMock.mockResolvedValueOnce({
      data: {
        id: "doc-1",
        title: "My resume",
        doc_type: "resume",
        file_name: "resume.pdf",
        file_size_kb: 12,
        status: "processing",
        created_at: "2026-07-04T00:00:00Z",
      },
    })

    const file = new File([new Blob(["abc"])], "resume.pdf", {
      type: "application/pdf",
    })

    const result = await uploadDocument(file, {
      title: "My resume",
      doc_type: "resume",
      client_id: "default",
    })

    expect(postMock).toHaveBeenCalledTimes(1)
    const [path, form, config] = postMock.mock.calls[0]
    expect(path).toBe("/api/v1/documents/upload")
    expect(form).toBeInstanceOf(FormData)
    expect(form.get("file")).toBe(file)
    expect(form.get("title")).toBe("My resume")
    expect(form.get("doc_type")).toBe("resume")
    expect(form.get("client_id")).toBe("default")
    expect(config.headers["Content-Type"]).toBe("multipart/form-data")
    expect(result.id).toBe("doc-1")
    expect(result.status).toBe("processing")
  })

  it("propagates the underlying API error", async () => {
    postMock.mockRejectedValueOnce(new Error("boom"))
    const file = new File([new Blob(["x"])], "resume.pdf", {
      type: "application/pdf",
    })
    await expect(
      uploadDocument(file, {
        title: "t",
        doc_type: "resume",
        client_id: "default",
      })
    ).rejects.toThrow("boom")
  })
})

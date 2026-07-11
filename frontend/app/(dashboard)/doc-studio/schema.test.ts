import { describe, it, expect } from "vitest"
import { metadataItemSchema } from "./schema"
import { MAX_FILE_SIZE } from "./components/file-dropzone"

const validBase = {
  title: "Resume",
  doc_type: "resume" as const,
  client_id: "11111111-1111-1111-1111-111111111111",
}

function makeFile(size: number, type = "application/pdf", name = "file.pdf"): File {
  return new File([new Uint8Array(size)], name, { type })
}

describe("metadataItemSchema file validation", () => {
  it("accepts a PDF under the size limit", () => {
    const result = metadataItemSchema.safeParse({ ...validBase, file: makeFile(1024) })
    expect(result.success).toBe(true)
  })

  it("rejects a file over the shared MAX_FILE_SIZE limit", () => {
    const result = metadataItemSchema.safeParse({
      ...validBase,
      file: makeFile(MAX_FILE_SIZE + 1),
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].path).toEqual(["file"])
      expect(result.error.issues[0].message).toMatch(/20 MB/)
    }
  })

  it("rejects a disallowed file type", () => {
    const result = metadataItemSchema.safeParse({
      ...validBase,
      file: makeFile(1024, "text/plain", "notes.txt"),
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toMatch(/PDF and DOCX/)
    }
  })

  it("allows a missing file (added later in the flow)", () => {
    const result = metadataItemSchema.safeParse(validBase)
    expect(result.success).toBe(true)
  })
})

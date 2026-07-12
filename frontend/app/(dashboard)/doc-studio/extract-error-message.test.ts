import { describe, it, expect } from "vitest"
import { AxiosError } from "axios"
import { extractErrorMessage } from "./page"

function axiosErrorWithStatus(status: number, detail: string): AxiosError {
  return new AxiosError("Request failed", "ERR_BAD_REQUEST", undefined, undefined, {
    status,
    statusText: "",
    headers: {},
    config: {} as never,
    data: { detail },
  })
}

describe("extractErrorMessage", () => {
  it("surfaces the backend's message for a 413 (file too large) response", () => {
    const err = axiosErrorWithStatus(413, "File exceeds the 20 MB size limit")
    expect(extractErrorMessage(err)).toBe("File exceeds the 20 MB size limit")
  })

  it("surfaces the backend's message for a 415 (unsupported type) response", () => {
    const err = axiosErrorWithStatus(415, "Only PDF and DOCX files are allowed")
    expect(extractErrorMessage(err)).toBe("Only PDF and DOCX files are allowed")
  })
})

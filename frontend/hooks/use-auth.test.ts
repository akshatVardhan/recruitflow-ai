import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"

const postMock = vi.fn()
vi.mock("@/lib/api", () => ({
  default: { post: (...args: unknown[]) => postMock(...args) },
  setAccessToken: vi.fn(),
}))

const getMeMock = vi.fn()
const registerUserMock = vi.fn()
vi.mock("@/lib/api/auth", () => ({
  getMe: (...args: unknown[]) => getMeMock(...args),
  registerUser: (...args: unknown[]) => registerUserMock(...args),
}))

import { useAuth } from "./use-auth"

const MOCK_USER = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "ada@example.com",
  full_name: "Ada Lovelace",
  is_active: true,
}

describe("useAuth session restore (RF-71)", () => {
  beforeEach(() => {
    getMeMock.mockReset()
    postMock.mockReset()
  })

  it("starts initializing and restores the user when a valid session exists", async () => {
    getMeMock.mockResolvedValueOnce(MOCK_USER)
    const { result } = renderHook(() => useAuth())

    expect(result.current.isInitializing).toBe(true)
    expect(result.current.user).toBeNull()
    // isLoading (form-submit state) must stay false during restore - it's a
    // distinct concern, not "signing in".
    expect(result.current.isLoading).toBe(false)

    await waitFor(() => expect(result.current.isInitializing).toBe(false))
    expect(result.current.user).toEqual(MOCK_USER)
  })

  it("stays logged out without surfacing an error when no session exists", async () => {
    getMeMock.mockRejectedValueOnce(new Error("401"))
    const { result } = renderHook(() => useAuth())

    await waitFor(() => expect(result.current.isInitializing).toBe(false))
    expect(result.current.user).toBeNull()
    expect(result.current.error).toBeNull()
  })
})

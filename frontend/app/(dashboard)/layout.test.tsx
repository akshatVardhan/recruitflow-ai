import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"

const replaceMock = vi.fn()
vi.mock("next/navigation", () => ({
  usePathname: () => "/doc-studio",
  useRouter: () => ({ replace: replaceMock }),
}))

const useAuthMock = vi.fn()
vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => useAuthMock(),
}))

import DashboardLayout from "./layout"

describe("DashboardLayout route guard (RF-72)", () => {
  beforeEach(() => {
    replaceMock.mockReset()
  })

  it("renders nothing and does not redirect while the session restore is in flight", () => {
    useAuthMock.mockReturnValue({ user: null, isInitializing: true })
    const { container } = render(<DashboardLayout>content</DashboardLayout>)
    expect(container).toBeEmptyDOMElement()
    expect(replaceMock).not.toHaveBeenCalled()
  })

  it("redirects to /login once restore settles with no session", async () => {
    useAuthMock.mockReturnValue({ user: null, isInitializing: false })
    render(<DashboardLayout>content</DashboardLayout>)
    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/login"))
  })

  it("renders the dashboard chrome and children once a session is restored", () => {
    useAuthMock.mockReturnValue({
      user: { id: "1", email: "a@b.com", full_name: "A", is_active: true },
      isInitializing: false,
    })
    render(<DashboardLayout>dashboard content</DashboardLayout>)
    expect(screen.getByText("dashboard content")).toBeInTheDocument()
    expect(replaceMock).not.toHaveBeenCalled()
  })
})

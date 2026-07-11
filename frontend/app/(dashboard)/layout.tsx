"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Toaster } from "@/components/ui/toaster"
import { useAuth } from "@/hooks/use-auth"
import { FileText, Users, Briefcase, Search, MessageSquare, Menu, X, Building2 } from "lucide-react"

const navItems = [
  { href: "/doc-studio", label: "Doc Studio", icon: FileText },
  { href: "/ats", label: "ATS", icon: Users },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/talent-finder", label: "Talent Finder", icon: Search },
  { href: "/job-finder", label: "Job Finder", icon: Briefcase },
  { href: "/chat", label: "Chat", icon: MessageSquare },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  // RF-72: route guard for dashboard pages. Deliberately NOT a
  // frontend/middleware.ts edge check - in production the refresh-token
  // cookie is scoped to the backend's own Cloud Run origin (SameSite=None,
  // cross-origin from the Vercel-hosted frontend per ADR-008), so Next.js
  // middleware running on the frontend's server would never see it and
  // would permanently redirect every legitimately logged-in user to
  // /login. useAuth's session restore (RF-71) already makes the real,
  // cross-origin-safe check by calling the backend directly; this guard
  // just acts on that result.
  const { user, isInitializing } = useAuth()

  useEffect(() => {
    if (!isInitializing && !user) {
      router.replace("/login")
    }
  }, [isInitializing, user, router])

  if (isInitializing || !user) {
    // Avoid flashing protected content while the session restore is still
    // in flight, or during the redirect above.
    return null
  }

  return (
    <div className="flex h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r bg-background transition-transform md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center border-b px-4">
          <Building2 className="h-5 w-5 mr-2" />
          <span className="font-semibold">RecruitFlow AI</span>
        </div>
        <nav className="space-y-1 p-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                pathname.startsWith(item.href)
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center border-b px-4">
          <button
            className="mr-2 md:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <span className="text-sm text-muted-foreground">Active Client: Placeholder</span>
        </header>
        <main className="flex-1 overflow-auto p-4">{children}</main>
      </div>
      <Toaster />
    </div>
  )
}

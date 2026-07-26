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

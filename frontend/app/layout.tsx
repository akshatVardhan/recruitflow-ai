import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "RecruitFlow AI",
  description: "AI-powered recruitment platform",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

"use client"

import { useState } from "react"
import { getAccessToken } from "@/lib/api"

export function useStream() {
  const [content, setContent] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)

  const startStream = async (endpoint: string, body: object) => {
    setIsStreaming(true)
    setContent("")
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify(body),
      })
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split("\n\n")
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            setContent((prev) => prev + line.slice(6))
          }
        }
      }
    } catch {
      setContent("Error: Failed to stream response")
    }
    setIsStreaming(false)
  }

  return { content, isStreaming, startStream }
}

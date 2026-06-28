"use client"

import { useState, useCallback } from "react"
import api, { setAccessToken } from "@/lib/api"

interface User {
  id: string
  email: string
  full_name: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  error: string | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: false,
    error: null,
  })

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const { data } = await api.post("/api/v1/auth/login", { email, password })
      setAccessToken(data.access_token)
      setState({ user: data.user, isLoading: false, error: null })
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: "Invalid credentials",
      }))
    }
  }, [])

  const logout = useCallback(() => {
    setAccessToken(null)
    setState({ user: null, isLoading: false, error: null })
  }, [])

  return { ...state, login, logout }
}

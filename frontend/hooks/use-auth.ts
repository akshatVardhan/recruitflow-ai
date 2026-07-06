"use client"

import { useState, useCallback } from "react"
import api, { setAccessToken } from "@/lib/api"
import { registerUser } from "@/lib/api/auth"
import type { LoginResponse, User } from "@/types/api"

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
      const { data } = await api.post<LoginResponse>("/api/v1/auth/login", {
        email,
        password,
      })
      setAccessToken(data.access_token)
      setState({ user: data.user, isLoading: false, error: null })
      return true
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: "Invalid credentials",
      }))
      return false
    }
  }, [])

  const register = useCallback(
    async (email: string, fullName: string, password: string) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }))
      try {
        await registerUser({ email, full_name: fullName, password })
        return await login(email, password)
      } catch {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: "Could not create account - the email may already be registered.",
        }))
        return false
      }
    },
    [login]
  )

  const logout = useCallback(() => {
    setAccessToken(null)
    setState({ user: null, isLoading: false, error: null })
    void api.post("/api/v1/auth/logout").catch(() => {
      // Best-effort: clear the local session even if the cookie-clear call fails.
    })
  }, [])

  return { ...state, login, register, logout }
}

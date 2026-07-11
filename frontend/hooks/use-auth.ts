"use client"

import { useState, useCallback, useEffect } from "react"
import api, { setAccessToken } from "@/lib/api"
import { getMe, registerUser } from "@/lib/api/auth"
import type { LoginResponse, User } from "@/types/api"

interface AuthState {
  user: User | null
  isLoading: boolean
  // RF-71: true until the mount-time session-restore attempt settles.
  // Kept separate from isLoading (which gates login/register submit
  // buttons) so the button doesn't briefly read "Signing in..." on every
  // page load while a background /auth/me check is still in flight.
  isInitializing: boolean
  error: string | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: false,
    isInitializing: true,
    error: null,
  })

  useEffect(() => {
    let cancelled = false
    getMe()
      .then((user) => {
        if (!cancelled) setState((prev) => ({ ...prev, user, isInitializing: false }))
      })
      .catch(() => {
        // No valid session (never logged in, or refresh cookie expired/
        // absent) - not an error to surface, just stay logged out.
        if (!cancelled) setState((prev) => ({ ...prev, isInitializing: false }))
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }))
    try {
      const { data } = await api.post<LoginResponse>("/api/v1/auth/login", {
        email,
        password,
      })
      setAccessToken(data.access_token)
      setState((prev) => ({ ...prev, user: data.user, isLoading: false, error: null }))
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
    setState((prev) => ({ ...prev, user: null, isLoading: false, error: null }))
    void api.post("/api/v1/auth/logout").catch(() => {
      // Best-effort: clear the local session even if the cookie-clear call fails.
    })
  }, [])

  return { ...state, login, register, logout }
}

import api from "@/lib/api"
import type { RegisterRequest, User } from "@/types/api"

export async function registerUser(payload: RegisterRequest): Promise<User> {
  const { data } = await api.post<User>("/api/v1/auth/register", payload)
  return data
}

// RF-71: called with no access token in memory on a fresh page load - the
// api.ts response interceptor transparently attempts a refresh via the
// httpOnly cookie on the resulting 401 and retries this call, so it either
// resolves with the restored user or rejects when no valid session exists.
export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/api/v1/auth/me")
  return data
}

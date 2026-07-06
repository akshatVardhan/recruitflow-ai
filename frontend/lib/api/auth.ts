import api from "@/lib/api"
import type { RegisterRequest, User } from "@/types/api"

export async function registerUser(payload: RegisterRequest): Promise<User> {
  const { data } = await api.post<User>("/api/v1/auth/register", payload)
  return data
}

import api from "@/lib/api"
import type { Client, ClientCreate } from "@/types/api"

const CLIENTS_PATH = "/api/v1/clients"

export async function listClients(): Promise<Client[]> {
  const { data } = await api.get<Client[]>(CLIENTS_PATH)
  return data
}

export async function createClient(payload: ClientCreate): Promise<Client> {
  const { data } = await api.post<Client>(CLIENTS_PATH, payload)
  return data
}

export interface HealthResponse {
  status: string
  version: string
}

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
}

export interface Document {
  id: string
  client_id: string
  title: string
  doc_type: string
  file_name: string
  created_at: string
}

export interface Candidate {
  id: string
  full_name: string
  email: string
  phone: string
  source: string
}

export interface Job {
  id: string
  client_id: string
  title: string
  department: string
  location: string
  status: string
}

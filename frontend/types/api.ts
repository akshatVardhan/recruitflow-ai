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

export interface RegisterRequest {
  email: string
  full_name: string
  password: string
}

export interface LoginResponse {
  // The refresh token is never in the body - it's set as an httpOnly
  // cookie by the backend, invisible to JS.
  access_token: string
  token_type: string
  user: User
}

export interface Client {
  id: string
  name: string
  industry: string | null
  is_active: boolean
  created_at: string
}

export interface ClientCreate {
  name: string
  industry?: string
}

export type DocType =
  | "resume"
  | "job_description"
  | "offer_letter"
  | "sop"
  | "performance_report"
  | "policy"
  | "contract"
  | "other"

export const DOC_TYPE_VALUES: { value: DocType; label: string }[] = [
  { value: "resume", label: "Resume" },
  { value: "job_description", label: "Job Description" },
  { value: "offer_letter", label: "Offer Letter" },
  { value: "sop", label: "SOP" },
  { value: "performance_report", label: "Performance Report" },
  { value: "policy", label: "Policy" },
  { value: "contract", label: "Contract" },
  { value: "other", label: "Other" },
]

export interface UploadMetadata {
  title: string
  doc_type: DocType
  client_id: string
}

export interface UploadResponse {
  id: string
  title: string
  doc_type: string
  file_name: string
  file_size_kb: number | null
  status: string
  created_at: string
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

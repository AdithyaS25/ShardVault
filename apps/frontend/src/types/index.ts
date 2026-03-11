// ─── Auth ────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string
  password: string
}

export interface RegisterResponse {
  success: boolean
  message: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface LogoutResponse {
  success: boolean
  message: string
}

export interface MeResponse {
  id: string
  email: string
  role: "user" | "admin"
}

// ─── Crypto ──────────────────────────────────────────────────────────────────

export interface EncryptRequest {
  plaintext: string
  master_password: string
  salt_hex?: string
}

export interface EncryptResponse {
  encrypted_payload: string
  salt_hex: string
  algorithm: string
  payload_metadata: {
    algorithm: string
    total_bytes: number
    iv_bytes: number
    tag_bytes: number
    ciphertext_bytes: number
  }
}

export interface DecryptRequest {
  encrypted_payload: string
  master_password: string
  salt_hex: string
}

export interface DecryptResponse {
  plaintext: string
}

export interface CryptoHealthResponse {
  status: "ok" | "degraded"
  algorithm: string
  kdf: string
  test_passed: boolean
}

// ─── Shamir ───────────────────────────────────────────────────────────────────

export interface ShareDict {
  x: number
  y: string // base64
}

export interface SplitRequest {
  encrypted_payload: string
  vault_entry_id?: string
}

export interface SplitResponse {
  shares: ShareDict[]
  total_shares: number
  threshold: number
  secret_length: number
  vault_entry_id: string
}

export interface ReconstructRequest {
  shares: ShareDict[]
  secret_length: number
  vault_entry_id: string
}

export interface ReconstructResponse {
  encrypted_payload: string
  shares_used: number
  threshold: number
  vault_entry_id: string
}

export interface ShamirHealthResponse {
  status: "ok" | "degraded"
  total_shares: number
  threshold: number
  test_passed: boolean
}

export interface ShamirConfigResponse {
  total_shares: number
  threshold: number
  field: string
  irreducible_polynomial: string
}

// ─── App-level ────────────────────────────────────────────────────────────────

export interface VaultEntry {
  id: string
  label: string
  username?: string
  url?: string
  encrypted_payload: string
  secret_length: number
  salt_hex: string
  created_at: string
  updated_at?: string
}

export type UserRole = "user" | "admin"

export interface AuthState {
  user: MeResponse | null
  accessToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

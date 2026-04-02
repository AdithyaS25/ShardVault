import { apiClient } from './client'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface VaultEntryMeta {
  id: string
  site_name: string
  username: string
  label: string | null
  created_at: string
  updated_at: string
}

export interface VaultListResponse {
  success: boolean
  data: VaultEntryMeta[]
  total: number
  page: number
  page_size: number
}

export interface VaultCreateRequest {
  site_name: string
  username: string
  plaintext_password: string
  master_password: string
  label?: string
}

export interface VaultCreateResponse {
  success: boolean
  message: string
  vault_id: string
}

export interface VaultRetrieveResponse {
  success: boolean
  vault_id: string
  site_name: string
  username: string
  label: string | null
  plaintext_password: string
}

export interface VaultDeleteResponse {
  success: boolean
  message: string
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const vaultApi = {
  list: async (page = 1, page_size = 20): Promise<VaultListResponse> => {
    const { data } = await apiClient.get<VaultListResponse>('/vault', {
      params: { page, page_size },
    })
    return data
  },

  create: async (payload: VaultCreateRequest): Promise<VaultCreateResponse> => {
    const { data } = await apiClient.post<VaultCreateResponse>('/vault', payload)
    return data
  },

  retrieve: async (
    vault_id: string,
    master_password: string
  ): Promise<VaultRetrieveResponse> => {
    const { data } = await apiClient.get<VaultRetrieveResponse>(
      `/vault/${vault_id}`,
      { params: { master_password } }
    )
    return data
  },

  delete: async (vault_id: string): Promise<VaultDeleteResponse> => {
    const { data } = await apiClient.delete<VaultDeleteResponse>(
      `/vault/${vault_id}`
    )
    return data
  },
}
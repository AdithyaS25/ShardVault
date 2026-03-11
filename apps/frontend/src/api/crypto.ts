/**
 * api/crypto.ts — ShardVault Frontend
 * Mirrors endpoints from app/crypto/routes.py
 */

import apiClient from "./client"
import type {
  EncryptRequest,
  EncryptResponse,
  DecryptRequest,
  DecryptResponse,
  CryptoHealthResponse,
} from "@/types"

export const cryptoApi = {
  /** POST /crypto/encrypt — requires Bearer token */
  encrypt: async (data: EncryptRequest): Promise<EncryptResponse> => {
    const res = await apiClient.post<EncryptResponse>("/crypto/encrypt", data)
    return res.data
  },

  /** POST /crypto/decrypt — requires Bearer token */
  decrypt: async (data: DecryptRequest): Promise<DecryptResponse> => {
    const res = await apiClient.post<DecryptResponse>("/crypto/decrypt", data)
    return res.data
  },

  /** GET /crypto/health — public */
  health: async (): Promise<CryptoHealthResponse> => {
    const res = await apiClient.get<CryptoHealthResponse>("/crypto/health")
    return res.data
  },
}

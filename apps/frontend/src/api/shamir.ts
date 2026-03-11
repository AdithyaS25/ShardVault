/**
 * api/shamir.ts — ShardVault Frontend
 * Mirrors endpoints from app/shamir/routes.py
 */

import apiClient from "./client"
import type {
  SplitRequest,
  SplitResponse,
  ReconstructRequest,
  ReconstructResponse,
  ShamirHealthResponse,
  ShamirConfigResponse,
} from "@/types"

export const shamirApi = {
  /** POST /shamir/split — requires Bearer token */
  split: async (data: SplitRequest): Promise<SplitResponse> => {
    const res = await apiClient.post<SplitResponse>("/shamir/split", data)
    return res.data
  },

  /** POST /shamir/reconstruct — requires Bearer token */
  reconstruct: async (data: ReconstructRequest): Promise<ReconstructResponse> => {
    const res = await apiClient.post<ReconstructResponse>("/shamir/reconstruct", data)
    return res.data
  },

  /** GET /shamir/health — public */
  health: async (): Promise<ShamirHealthResponse> => {
    const res = await apiClient.get<ShamirHealthResponse>("/shamir/health")
    return res.data
  },

  /** GET /shamir/config — public */
  config: async (): Promise<ShamirConfigResponse> => {
    const res = await apiClient.get<ShamirConfigResponse>("/shamir/config")
    return res.data
  },
}

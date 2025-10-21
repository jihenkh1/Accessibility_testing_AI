import axios from 'axios'

// Prefer explicit API URL if provided, else fallback to Vite dev proxy (/api)
const BASE_URL = (import.meta as any)?.env?.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300_000, // 5 minutes for long-running scans
})

export type AnalyzeRequest = {
  report: Record<string, any>
  framework?: string
  use_ai?: boolean
  max_ai_issues?: number | null
  url?: string
}

export async function postScan(req: AnalyzeRequest) {
  const res = await api.post('/scans', req)
  return res.data as {
    scan_id?: number
    summary: Record<string, any>
    issues: Array<Record<string, any>>
  }
}

export async function listScans() {
  try {
    const res = await api.get('/scans')
    return res.data as Array<Record<string, any>>
  } catch (err) {
    // Gracefully degrade when backend is unavailable so the Dashboard can render
    return []
  }
}

export async function getScan(id: number) {
  const res = await api.get(`/scans/${id}`)
  return res.data as Record<string, any>
}

export async function listScanIssues(id: number, size: number = 500) {
  try {
    const res = await api.get(`/scans/${id}/issues`, { params: { page: 1, size } })
    return res.data as { items: Array<Record<string, any>>; total: number }
  } catch (err) {
    return { items: [], total: 0 }
  }
}

// AI Usage Statistics
export async function getAIUsageStats() {
  try {
    const res = await api.get('/ai/usage-stats')
    return res.data as {
      available: boolean
      stats?: {
        total_requests: number
        successful_requests: number
        failed_requests: number
        total_prompt_tokens: number
        total_completion_tokens: number
        total_tokens: number
        estimated_cost_usd: number
        success_rate: number
      }
      error?: string
    }
  } catch (err) {
    return { available: false, error: String(err) }
  }
}

export async function resetAIUsageStats() {
  const res = await api.post('/ai/usage-stats/reset')
  return res.data as { success: boolean; message?: string; error?: string }
}

// AI Cache Statistics
export async function getAICacheStats() {
  try {
    const res = await api.get('/ai/cache-stats')
    return res.data as {
      available: boolean
      stats?: {
        total_entries: number
        valid_entries: number
        expired_entries: number
        oldest_entry: string | null
        newest_entry: string | null
        ttl_days: number
      }
      error?: string
    }
  } catch (err) {
    return { available: false, error: String(err) }
  }
}

export async function cleanupAICache() {
  const res = await api.post('/ai/cache/cleanup')
  return res.data as { success: boolean; deleted?: number; message?: string; error?: string }
}


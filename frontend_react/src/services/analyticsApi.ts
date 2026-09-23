import { api } from '../lib/api'

export interface AnalyticsSummary {
  total_resumes: number
  processed_resumes: number
  processing_rate_pct: number
  total_active_jobs: number
  total_candidates: number
  pending_reviews: number
  model_unavailable_count: number
}

export const getAnalyticsSummary = async (): Promise<AnalyticsSummary> => {
  const response = await api.get('/analytics/summary')
  return response.data
}

export interface AuditEvent {
  id: number
  event_type: string
  summary: string
  actor_email: string
  resource_type: string
  resource_id: string
  outcome: string
  ip_address: string
  occurred_at: string
}

export interface AuditLogsResponse {
  total: number
  page: number
  page_size: number
  events: AuditEvent[]
}

export const getAuditLogs = async (limit: number = 10): Promise<AuditLogsResponse> => {
  const response = await api.get(`/admin/audit-logs?page=1&page_size=${limit}`)
  return response.data
}

export interface ModelVersion {
  id: number
  version_tag: string
  test_accuracy: number
  test_macro_f1: number
  is_active: boolean
}

export const getModelVersions = async (): Promise<ModelVersion[]> => {
  const response = await api.get('/admin/model-versions')
  return response.data
}

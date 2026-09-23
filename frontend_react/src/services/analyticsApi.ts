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

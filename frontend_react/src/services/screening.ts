import { api } from '../lib/api'

export interface Resume {
  id: number
  public_id: string
  candidate_id: number | null
  original_filename: string
  file_size_bytes: number
  page_count: number | null
  status: string
  error_message: string | null
  text_char_count: number | null
  predicted_domain: string | null
  prediction_confidence: string | null
  uploaded_at: string
  processed_at: string | null
}

export interface ExtractedSkill {
  id: number
  canonical_name: string
  matched_text: string
  domain: string | null
  category: string | null
  evidence_snippet: string | null
  extraction_method: string
  frequency: number
}

export interface ResumeDetail extends Resume {
  extracted_skills: ExtractedSkill[]
}

export const getResumes = async (): Promise<Resume[]> => {
  const response = await api.get('/resumes')
  return response.data
}

export const getResumeDetail = async (id: string): Promise<ResumeDetail> => {
  const response = await api.get(`/resumes/${id}`)
  return response.data
}

export const getScreeningResults = async (jobId: string): Promise<any[]> => {
  const response = await api.get(`/screening/${jobId}/results`)
  return response.data
}

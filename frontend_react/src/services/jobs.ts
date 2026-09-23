import { api } from '../lib/api'

export interface JobRequirement {
  skill_name: string
  is_required: boolean
  weight: number
  notes?: string
}

export interface Job {
  id: string
  title: string
  department: string
  description: string
  domain?: string
  is_active: boolean
  requirements: JobRequirement[]
}

export const getJobs = async (): Promise<Job[]> => {
  const response = await api.get('/jobs')
  return response.data
}

export const createJob = async (jobData: Omit<Job, 'id' | 'is_active'>): Promise<Job> => {
  const response = await api.post('/jobs', jobData)
  return response.data
}

export const deleteJob = async (jobId: string): Promise<void> => {
  await api.delete(`/jobs/${jobId}`)
}

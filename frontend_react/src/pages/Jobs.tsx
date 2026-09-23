import React, { useEffect, useState } from 'react'
import { getJobs, createJob, deleteJob } from '../services/jobs'
import type { Job } from '../services/jobs'
import { Briefcase, Plus, Trash2, MapPin, Tag } from 'lucide-react'

export function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // Form State
  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('')
  const [description, setDescription] = useState('')
  const [domain, setDomain] = useState('')
  
  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const data = await getJobs()
      setJobs(data)
    } catch (error) {
      console.error('Failed to fetch jobs', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createJob({
        title,
        department,
        description,
        domain,
        requirements: [] // simplify for now
      })
      setShowForm(false)
      fetchJobs()
    } catch (error) {
      console.error('Failed to create job', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this job?')) return
    try {
      await deleteJob(id)
      fetchJobs()
    } catch (error) {
      console.error('Failed to delete job', error)
    }
  }

  return (
    <div className="w-full h-full flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Jobs Management</h1>
          <p className="text-gray-400">Manage open positions and match parameters.</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-gradient-to-r from-primary to-accent rounded-lg text-sm text-white font-semibold hover:opacity-90 transition-opacity flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          {showForm ? 'Cancel' : 'New Job'}
        </button>
      </div>

      {showForm && (
        <div className="glass-card p-6 rounded-2xl border border-primary/20">
          <h2 className="text-xl font-bold text-white mb-4">Create New Job Posting</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Job Title</label>
                <input required value={title} onChange={e => setTitle(e.target.value)} className="w-full bg-surface/50 border border-white/10 rounded-lg px-3 py-2 text-white" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Department</label>
                <input required value={department} onChange={e => setDepartment(e.target.value)} className="w-full bg-surface/50 border border-white/10 rounded-lg px-3 py-2 text-white" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Domain (e.g. AI, Backend)</label>
                <input value={domain} onChange={e => setDomain(e.target.value)} className="w-full bg-surface/50 border border-white/10 rounded-lg px-3 py-2 text-white" />
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea required value={description} onChange={e => setDescription(e.target.value)} rows={4} className="w-full bg-surface/50 border border-white/10 rounded-lg px-3 py-2 text-white custom-scrollbar" />
            </div>
            <button type="submit" className="px-6 py-2 bg-primary text-white rounded-lg font-medium">Save Job</button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-gray-400">Loading jobs...</div>
      ) : jobs.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center glass-card rounded-2xl border border-white/5">
          <Briefcase className="w-12 h-12 text-gray-500 mb-4" />
          <h3 className="text-xl font-semibold text-white">No Jobs Found</h3>
          <p className="text-gray-400 mt-2">Create your first job posting to start matching candidates.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {jobs.map(job => (
            <div key={job.id} className="glass-card rounded-xl p-6 border border-white/5 relative group">
              <button 
                onClick={() => handleDelete(job.id)}
                className="absolute top-4 right-4 p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              
              <h3 className="text-xl font-bold text-white mb-2 pr-8">{job.title}</h3>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="flex items-center gap-1 text-xs bg-primary/20 text-primary px-2 py-1 rounded">
                  <MapPin className="w-3 h-3" />
                  {job.department}
                </span>
                {job.domain && (
                  <span className="flex items-center gap-1 text-xs bg-accent/20 text-accent px-2 py-1 rounded">
                    <Tag className="w-3 h-3" />
                    {job.domain}
                  </span>
                )}
              </div>
              <p className="text-gray-400 text-sm line-clamp-3">{job.description}</p>
              
              <div className="mt-6 pt-4 border-t border-white/5">
                <div className="text-sm font-medium text-gray-300">Requirements: {job.requirements?.length || 0} skills</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

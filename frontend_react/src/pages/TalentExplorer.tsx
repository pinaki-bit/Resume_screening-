import React, { useState, useEffect } from 'react'
import { Search, Filter, Briefcase, MapPin, GraduationCap, Award, CheckCircle } from 'lucide-react'
import { getResumes, getResumeDetail } from '../services/screening'
import type { Resume, ResumeDetail } from '../services/screening'

export function TalentExplorer() {
  const [searchTerm, setSearchTerm] = useState('')
  const [resumes, setResumes] = useState<Resume[]>([])
  const [selectedResume, setSelectedResume] = useState<ResumeDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchResumes()
  }, [])

  const fetchResumes = async () => {
    try {
      const data = await getResumes()
      setResumes(data)
      if (data.length > 0) {
        handleSelectResume(data[0].public_id)
      }
    } catch (error) {
      console.error('Failed to fetch resumes', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectResume = async (id: string) => {
    try {
      const detail = await getResumeDetail(id)
      setSelectedResume(detail)
    } catch (error) {
      console.error('Failed to fetch resume detail', error)
    }
  }

  // Filter based on candidate name or skills (if available in summary list)
  const filteredResumes = resumes.filter(r => 
    r.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="w-full h-full flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Talent Explorer</h1>
          <p className="text-gray-400">Discover and analyze candidate profiles with AI matching.</p>
        </div>
        <button className="px-4 py-2 bg-surface border border-white/10 rounded-lg text-sm text-white hover:bg-white/5 transition-colors flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Advanced Filters
        </button>
      </div>
      
      {/* Search Bar */}
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="w-full pl-11 pr-4 py-4 bg-surface/80 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all shadow-lg shadow-black/20"
          placeholder="Search by filename or keywords..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-0">
        {/* Candidate List */}
        <div className="lg:w-1/3 w-full flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
          {loading ? (
             <div className="text-gray-400 p-4">Loading candidates...</div>
          ) : filteredResumes.length === 0 ? (
             <div className="text-gray-400 p-4">No candidates found. Upload a resume first.</div>
          ) : (
            filteredResumes.map((resume) => (
              <div 
                key={resume.public_id} 
                onClick={() => handleSelectResume(resume.public_id)}
                className={`glass-card rounded-xl p-5 cursor-pointer border relative overflow-hidden group ${selectedResume?.public_id === resume.public_id ? 'border-primary bg-primary/10' : 'border-primary/20 bg-primary/5'}`}
              >
                <div className="absolute top-0 right-0 p-3">
                   <div className="flex items-center justify-center w-10 h-10 rounded-full bg-surface border border-primary/30 shadow-[0_0_10px_rgba(59,130,246,0.3)]">
                      <CheckCircle className="w-4 h-4 text-primary" />
                   </div>
                </div>
                <h3 className="text-lg font-semibold text-white mb-1 truncate pr-12">{resume.original_filename}</h3>
                <p className="text-sm text-primary mb-2">Status: {resume.status}</p>
                <p className="text-xs text-gray-400">Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}</p>
              </div>
            ))
          )}
        </div>

        {/* Candidate Intelligence Detail */}
        <div className="lg:w-2/3 w-full glass-card rounded-2xl flex flex-col overflow-hidden">
          {selectedResume ? (
            <>
              {/* Header */}
              <div className="p-8 border-b border-white/5 bg-gradient-to-b from-surface/80 to-surface/40">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1">{selectedResume.original_filename}</h2>
                    <p className="text-primary text-lg">{selectedResume.predicted_domain || 'Domain Pending'}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                      {selectedResume.status}
                    </div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mt-1">Status</p>
                  </div>
                </div>
                
                <div className="flex gap-6 text-sm text-gray-300">
                  <div className="flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-gray-500" />
                      Confidence: {selectedResume.prediction_confidence || 'N/A'}
                  </div>
                  <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-gray-500" />
                      Size: {(selectedResume.file_size_bytes / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>

              <div className="p-8 overflow-y-auto flex-1 space-y-8 custom-scrollbar">
                {/* Skill Heatmap */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Award className="w-5 h-5 text-accent" />
                    Extracted Skills Intelligence
                  </h3>
                  {selectedResume.extracted_skills && selectedResume.extracted_skills.length > 0 ? (
                    <div className="grid grid-cols-2 gap-4">
                      {selectedResume.extracted_skills.map(skill => (
                        <div key={skill.id} className="bg-surface/50 p-4 rounded-xl border border-white/5">
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-gray-200">{skill.canonical_name}</span>
                            <span className="text-sm text-primary">{skill.frequency} mentions</span>
                          </div>
                          <div className="text-xs text-gray-400 mb-2 truncate">
                            {skill.category || 'Uncategorized'} - {skill.domain || 'Generic'}
                          </div>
                          <div className="w-full bg-black/50 rounded-full h-1.5 overflow-hidden">
                            <div className="h-1.5 rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${Math.min(100, skill.frequency * 20)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400 text-sm">No skills were extracted or extraction is still pending.</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 flex items-center justify-center h-full text-gray-500">
              Select a candidate from the list to view intelligence details.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

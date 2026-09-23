import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import React, { useEffect, useState } from 'react'
import { Layout } from './components/Layout'
import { IntelligenceCore } from './components/3d/IntelligenceCore'
import { UploadPortal } from './pages/UploadPortal'
import { TalentExplorer } from './pages/TalentExplorer'
import { AdminAnalytics } from './pages/AdminAnalytics'
import { Login } from './pages/Login'
import { Jobs } from './pages/Jobs'
import { getAnalyticsSummary } from './services/analyticsApi'
import type { AnalyticsSummary } from './services/analyticsApi'

// Simple Auth Wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Layout>{children}</Layout>
}

function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await getAnalyticsSummary()
        setSummary(data)
      } catch (e) {
        console.error('Failed to fetch summary', e)
      }
    }
    fetchSummary()
  }, [])

  return (
    <div className="w-full h-full flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Intelligence Dashboard</h1>
          <p className="text-gray-400">System active. Processing neural pathways.</p>
        </div>
      </div>
      
      <div className="flex-1 w-full flex flex-col lg:flex-row gap-6 min-h-[400px]">
        {/* 3D Core Container */}
        <div className="lg:w-1/2 w-full h-[400px] lg:h-full glass-card rounded-2xl overflow-hidden relative flex flex-col">
          <div className="absolute top-4 left-4 z-10">
            <h3 className="text-sm font-semibold text-primary/80 uppercase tracking-widest">Model Status</h3>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_#4ade80]" />
              <span className="text-xs text-gray-300">ONLINE - Calibration Stable</span>
            </div>
          </div>
          <div className="flex-1 w-full relative">
             <IntelligenceCore />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="lg:w-1/2 w-full flex flex-col gap-6">
          <div className="glass-card rounded-2xl p-6 flex-1">
            <h3 className="text-lg font-semibold text-white mb-4">Pipeline Status</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">Total Resumes Ingested</span>
                  <span className="text-gray-400">{summary?.total_resumes || 0}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">Processed Resumes</span>
                  <span className="text-gray-400">{summary?.processed_resumes || 0}</span>
                </div>
                <div className="w-full bg-surface rounded-full h-2 overflow-hidden border border-white/5">
                  <div className={`bg-primary h-2 rounded-full transition-all duration-1000`} style={{ width: `${summary?.processing_rate_pct || 0}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">Active Job Postings</span>
                  <span className="text-gray-400">{summary?.total_active_jobs || 0}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">Total Candidates</span>
                  <span className="text-gray-400">{summary?.total_candidates || 0}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="glass-card rounded-2xl p-6 flex-1">
            <h3 className="text-lg font-semibold text-white mb-4">Action Items</h3>
            <div className="space-y-4">
               <div className="flex justify-between items-center bg-surface/50 p-3 rounded-lg border border-white/5">
                  <span className="text-sm text-gray-300">Pending Reviews</span>
                  <span className="text-sm font-bold text-accent bg-accent/20 px-2 py-1 rounded">{summary?.pending_reviews || 0}</span>
               </div>
               <div className="flex justify-between items-center bg-surface/50 p-3 rounded-lg border border-white/5">
                  <span className="text-sm text-gray-300">Model Failures</span>
                  <span className="text-sm font-bold text-red-400 bg-red-400/20 px-2 py-1 rounded">{summary?.model_unavailable_count || 0}</span>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center w-full h-full">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-4">{title}</h1>
        <p className="text-gray-400">Module under construction.</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes inside Layout */}
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><UploadPortal /></ProtectedRoute>} />
        <Route path="/jobs" element={<ProtectedRoute><Jobs /></ProtectedRoute>} />
        <Route path="/explorer" element={<ProtectedRoute><TalentExplorer /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><AdminAnalytics /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><AdminAnalytics /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

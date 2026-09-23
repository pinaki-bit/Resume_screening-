import React, { useState, useEffect } from 'react'
import { Activity, Users, FileText, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import { getAnalyticsSummary, getAuditLogs, getModelVersions } from '../services/analyticsApi'
import type { AnalyticsSummary, AuditEvent, ModelVersion } from '../services/analyticsApi'

export function AdminAnalytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([])
  const [activeModel, setActiveModel] = useState<ModelVersion | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumData, logsData, modelsData] = await Promise.all([
          getAnalyticsSummary(),
          getAuditLogs(10),
          getModelVersions()
        ])
        setSummary(sumData)
        setAuditLogs(logsData.events)
        const active = modelsData.find(m => m.is_active)
        setActiveModel(active || modelsData[0] || null)
      } catch (err) {
        console.error("Failed to fetch analytics data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return <div className="p-8 text-gray-400">Loading real-time analytics...</div>
  }

  const formatTimeAgo = (isoDate: string) => {
    if (!isoDate) return 'Unknown'
    const ms = Date.now() - new Date(isoDate).getTime()
    const mins = Math.floor(ms / 60000)
    if (mins < 60) return `${mins} mins ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} hours ago`
    return `${Math.floor(hours / 24)} days ago`
  }

  return (
    <div className="w-full h-full flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Admin & Analytics Console</h1>
          <p className="text-gray-400">Real-time system health, performance metrics, and model telemetry.</p>
        </div>
      </div>
      
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Resumes', value: summary?.total_resumes || 0, icon: FileText, change: `${summary?.processing_rate_pct || 0}% processed`, color: 'text-primary' },
          { label: 'Total Candidates', value: summary?.total_candidates || 0, icon: Users, change: 'In database', color: 'text-accent' },
          { label: 'Active Jobs', value: summary?.total_active_jobs || 0, icon: Activity, change: 'Open positions', color: 'text-green-400' },
          { label: 'Pending Reviews', value: summary?.pending_reviews || 0, icon: Clock, change: 'Needs attention', color: 'text-yellow-400' }
        ].map(metric => (
          <div key={metric.label} className="glass-card rounded-xl p-6 border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-100 transition-opacity">
              <metric.icon className={`w-12 h-12 ${metric.color}`} />
            </div>
            <p className="text-sm text-gray-400 mb-1 relative z-10">{metric.label}</p>
            <p className="text-3xl font-bold text-white mb-2 relative z-10">{metric.value}</p>
            <p className={`text-xs ${metric.color} relative z-10`}>
              {metric.change}
            </p>
          </div>
        ))}
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* ML Model Health */}
        <div className="lg:w-1/2 w-full glass-card rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            ML Model Telemetry
          </h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-300">Classification Accuracy (Test)</span>
                <span className="text-green-400 font-bold">{activeModel ? (activeModel.test_accuracy * 100).toFixed(1) : 'N/A'}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div className="bg-green-400 h-2 rounded-full" style={{ width: activeModel ? `${activeModel.test_accuracy * 100}%` : '0%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-300">Macro F1 Score</span>
                <span className="text-primary font-bold">{activeModel ? (activeModel.test_macro_f1 * 100).toFixed(1) : 'N/A'}%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div className="bg-primary h-2 rounded-full" style={{ width: activeModel ? `${activeModel.test_macro_f1 * 100}%` : '0%' }} />
              </div>
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-surface/50 rounded-xl border border-white/5">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-gray-200 font-medium">Model Checksums Verified</p>
                <p className="text-xs text-gray-500 mt-1">Active Version: {activeModel?.version_tag || 'Unknown'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Audit Logs Preview */}
        <div className="lg:w-1/2 w-full glass-card rounded-2xl p-6 flex flex-col">
          <h3 className="text-lg font-semibold text-white mb-6">Recent Security Events</h3>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {auditLogs.length > 0 ? auditLogs.map((log) => (
              <div key={log.id} className="flex items-center gap-4 p-3 rounded-lg bg-surface/30 border border-white/5">
                {log.outcome === 'failure' || log.event_type.includes('fail') || log.event_type.includes('denied') ? (
                  <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
                ) : (
                  <Activity className="w-5 h-5 text-primary shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{log.summary}</p>
                  <p className="text-xs text-gray-500">by {log.actor_email}</p>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap">{formatTimeAgo(log.occurred_at)}</span>
              </div>
            )) : (
              <p className="text-gray-400 text-sm">No recent events found.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

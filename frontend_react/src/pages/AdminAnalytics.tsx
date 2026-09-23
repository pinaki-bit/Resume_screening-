import React from 'react'
import { Activity, Users, FileText, Server, AlertTriangle, CheckCircle } from 'lucide-react'

export function AdminAnalytics() {
  return (
    <div className="w-full h-full flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Admin & Analytics Console</h1>
          <p className="text-gray-400">System health, performance metrics, and model telemetry.</p>
        </div>
      </div>
      
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Resumes', value: '14,235', icon: FileText, change: '+12%', color: 'text-primary' },
          { label: 'Active Users', value: '1,042', icon: Users, change: '+5%', color: 'text-accent' },
          { label: 'API Latency', value: '45ms', icon: Activity, change: '-2ms', color: 'text-green-400' },
          { label: 'System Load', value: '28%', icon: Server, change: '+1%', color: 'text-yellow-400' }
        ].map(metric => (
          <div key={metric.label} className="glass-card rounded-xl p-6 border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-100 transition-opacity">
              <metric.icon className={`w-12 h-12 ${metric.color}`} />
            </div>
            <p className="text-sm text-gray-400 mb-1 relative z-10">{metric.label}</p>
            <p className="text-3xl font-bold text-white mb-2 relative z-10">{metric.value}</p>
            <p className={`text-xs ${metric.change.startsWith('+') ? 'text-green-400' : 'text-primary'} relative z-10`}>
              {metric.change} this week
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
                <span className="text-gray-300">Classification Accuracy (F1)</span>
                <span className="text-green-400 font-bold">98.2%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div className="bg-green-400 h-2 rounded-full" style={{ width: '98.2%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-300">Entity Extraction Recall</span>
                <span className="text-primary font-bold">94.5%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div className="bg-primary h-2 rounded-full" style={{ width: '94.5%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-300">OCR Confidence (PyTesseract)</span>
                <span className="text-yellow-400 font-bold">82.1%</span>
              </div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div className="bg-yellow-400 h-2 rounded-full" style={{ width: '82.1%' }} />
              </div>
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-surface/50 rounded-xl border border-white/5">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-gray-200 font-medium">Model Checksums Verified</p>
                <p className="text-xs text-gray-500 mt-1">SHA-256 integrity checks passed for LinearSVC and spaCy artifacts.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Audit Logs Preview */}
        <div className="lg:w-1/2 w-full glass-card rounded-2xl p-6 flex flex-col">
          <h3 className="text-lg font-semibold text-white mb-6">Recent Security Events</h3>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {[
              { time: '10 mins ago', event: 'Failed login attempt', user: 'unknown', severity: 'warning' },
              { time: '45 mins ago', event: 'Job description updated', user: 'admin_sarah', severity: 'info' },
              { time: '2 hours ago', event: 'Bulk resume upload (250 items)', user: 'hr_manager', severity: 'info' },
              { time: '4 hours ago', event: 'Rate limit exceeded', user: 'IP 192.168.1.4', severity: 'warning' }
            ].map((log, i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-surface/30 border border-white/5">
                {log.severity === 'warning' ? (
                  <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
                ) : (
                  <Activity className="w-5 h-5 text-primary shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{log.event}</p>
                  <p className="text-xs text-gray-500">by {log.user}</p>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap">{log.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

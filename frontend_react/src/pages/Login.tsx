import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Activity, Lock, Mail, Eye, EyeOff } from 'lucide-react'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await api.post('/auth/login', {
        email,
        password
      })
      
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      
      // Navigate to dashboard
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md glass-card p-8 relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-accent/20 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10">
          <div className="flex justify-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-accent p-0.5 shadow-lg shadow-primary/20">
              <div className="w-full h-full bg-surface rounded-[14px] flex items-center justify-center">
                <Activity className="w-8 h-8 text-primary" />
              </div>
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-white text-center mb-2">Resume Intel Portal</h2>
          <p className="text-gray-400 text-center text-sm mb-8">Sign in to access the command center</p>

          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                {error}
              </div>
            )}
            
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-surface/50 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                placeholder="Email address"
              />
            </div>

            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-500" />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-10 py-3 border border-white/10 rounded-xl bg-surface/50 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                placeholder="Password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-300 focus:outline-none"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 border border-transparent rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-primary to-accent hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface focus:ring-primary transition-all disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
          
          <div className="mt-6 text-center text-xs text-gray-500">
            <p>Admin Default: admin@example.com / Admin123!</p>
          </div>
        </div>
      </div>
    </div>
  )
}

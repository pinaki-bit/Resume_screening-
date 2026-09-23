import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, FileUp, Briefcase, Search, Activity, Settings, User } from 'lucide-react'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs))
}

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Upload', path: '/upload', icon: FileUp },
  { name: 'Jobs', path: '/jobs', icon: Briefcase },
  { name: 'Talent Explorer', path: '/explorer', icon: Search },
  { name: 'Analytics', path: '/analytics', icon: Activity },
  { name: 'Admin', path: '/admin', icon: Settings },
]

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      
      {/* Sidebar / Navigation Rail */}
      <aside className="w-20 md:w-64 h-full glass-panel border-l-0 border-t-0 border-b-0 rounded-none z-20 flex flex-col items-center md:items-stretch py-6 transition-all duration-300">
        <div className="flex items-center justify-center md:justify-start px-6 mb-10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)] shrink-0">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="hidden md:block ml-3 font-semibold text-white tracking-wide">
            Resume Intel
          </span>
        </div>

        <nav className="flex-1 w-full px-4 space-y-2">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center px-4 py-3 rounded-lg transition-all duration-200 group relative",
                  isActive 
                    ? "bg-primary/20 text-primary shadow-[inset_4px_0_0_0_#3b82f6]" 
                    : "text-gray-400 hover:text-gray-200 hover:bg-surface/50"
                )}
              >
                <item.icon className={cn("w-5 h-5 shrink-0 transition-transform duration-200", isActive ? "scale-110" : "group-hover:scale-110")} />
                <span className="hidden md:block ml-3 font-medium text-sm">
                  {item.name}
                </span>
                
                {/* Tooltip for collapsed state on desktop/mobile */}
                <div className="md:hidden absolute left-full ml-4 px-2 py-1 bg-surface border border-white/10 rounded text-xs text-white opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {item.name}
                </div>
              </Link>
            )
          })}
        </nav>

        <div className="mt-auto px-4 w-full">
          <button className="w-full flex items-center px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-surface/50 transition-colors">
            <User className="w-5 h-5 shrink-0" />
            <span className="hidden md:block ml-3 font-medium text-sm">Profile</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-hidden flex flex-col relative z-10">
        {/* Top bar */}
        <header className="h-16 w-full glass-panel border-r-0 border-t-0 border-l-0 rounded-none flex items-center justify-end px-6 z-10 shrink-0">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-full bg-surface border border-white/10 flex items-center justify-center cursor-pointer hover:border-primary/50 transition-colors">
              <span className="text-xs font-semibold">AD</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-6 scroll-smooth">
          {children}
        </div>
      </main>

      {/* Background glow effects */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-[100px] pointer-events-none z-0" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent/10 blur-[100px] pointer-events-none z-0" />
    </div>
  )
}

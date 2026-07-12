import { LayoutDashboard, TrendingUp, BarChart3, Wallet, Activity, Settings } from 'lucide-react'

type Page = 'dashboard' | 'markets' | 'analysis' | 'trading' | 'portfolio'

const navItems = [
  { id: 'dashboard' as Page, label: 'Dashboard', icon: LayoutDashboard },
  { id: 'markets' as Page, label: 'Märkte', icon: TrendingUp },
  { id: 'analysis' as Page, label: 'Analyse', icon: BarChart3 },
  { id: 'trading' as Page, label: 'Trading', icon: Wallet },
  { id: 'portfolio' as Page, label: 'Portfolio', icon: Activity },
]

export default function Sidebar({
  currentPage,
  onNavigate,
}: {
  currentPage: Page
  onNavigate: (p: Page) => void
}) {
  return (
    <aside className="w-16 lg:w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2 px-3 lg:px-4 border-b border-gray-800">
        <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xs">
          CP
        </div>
        <span className="hidden lg:block text-sm font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          CryptoPulse AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                active
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span className="hidden lg:block">{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="p-2 border-t border-gray-800">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-800 text-sm">
          <Settings className="w-5 h-5 shrink-0" />
          <span className="hidden lg:block">Einstellungen</span>
        </button>
      </div>
    </aside>
  )
}
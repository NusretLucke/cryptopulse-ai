import { Bell, RefreshCw, Cpu } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getAIStatus } from '../../services/api'

type Page = 'dashboard' | 'markets' | 'analysis' | 'trading' | 'portfolio'

const pageTitles: Record<Page, string> = {
  dashboard: 'Dashboard',
  markets: 'Märkte',
  analysis: 'Analyse',
  trading: 'Trading',
  portfolio: 'Portfolio',
}

export default function Header({ currentPage }: { currentPage: Page }) {
  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: getAIStatus,
    refetchInterval: 15000,
  })

  return (
    <header className="h-14 bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 flex items-center justify-between px-4 lg:px-6 shrink-0">
      <h1 className="text-lg font-semibold">{pageTitles[currentPage]}</h1>

      <div className="flex items-center gap-3">
        {/* KI-Status */}
        {aiStatus && (
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
            aiStatus.status === 'warning' ? 'bg-amber-500/10 text-amber-400' :
            aiStatus.status === 'cautious' ? 'bg-red-500/10 text-red-400' :
            'bg-emerald-500/10 text-emerald-400'
          }`}>
            <Cpu className="w-3 h-3" />
            <span className="hidden sm:inline">
              {Math.round(aiStatus.win_rate * 100)}% Treffer
            </span>
          </div>
        )}

        {/* News Bell */}
        <button className="p-2 rounded-lg hover:bg-gray-800 text-gray-400">
          <Bell className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}
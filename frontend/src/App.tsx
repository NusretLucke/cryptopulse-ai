import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './components/dashboard/Dashboard'
import MarketDetail from './components/dashboard/MarketDetail'
import Sidebar from './components/common/Sidebar'
import Header from './components/common/Header'
import TradingPanel from './components/trading/TradingPanel'
import AnalysisPage from './components/analysis/AnalysisPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchInterval: 30000, retry: 2, staleTime: 10000 },
  },
})

type Page = 'dashboard' | 'markets' | 'analysis' | 'trading' | 'portfolio'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)

  const renderPage = () => {
    if (selectedSymbol) {
      return (
        <MarketDetail
          symbol={selectedSymbol}
          onBack={() => setSelectedSymbol(null)}
        />
      )
    }
    switch (page) {
      case 'dashboard':
        return <Dashboard onSelectCoin={setSelectedSymbol} />
      case 'markets':
        return <Dashboard onSelectCoin={setSelectedSymbol} showAll />
      case 'analysis':
        return <AnalysisPage onSelectCoin={setSelectedSymbol} />
      case 'trading':
        return <TradingPanel onSelectCoin={setSelectedSymbol} />
      case 'portfolio':
        return <TradingPanel onSelectCoin={setSelectedSymbol} showPortfolio />
      default:
        return <Dashboard onSelectCoin={setSelectedSymbol} />
    }
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen bg-gray-950 overflow-hidden">
        <Sidebar currentPage={page} onNavigate={setPage} />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header currentPage={page} />
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">
            {renderPage()}
          </main>
        </div>
      </div>
    </QueryClientProvider>
  )
}
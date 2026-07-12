import { useQuery } from '@tanstack/react-query'
import { getDashboard } from '../../services/api'
import { TrendingUp, TrendingDown, Wallet, Cpu, Newspaper, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import type { Market, TradeRecommendation } from '../../types/api'

function formatPrice(v: number | null) {
  if (v === null) return '—'
  return v >= 1 ? `€${v.toLocaleString('de-DE', { minimumFractionDigits: 2 })}` :
                  `€${v.toLocaleString('de-DE', { minimumFractionDigits: 6 })}`
}

function formatVolume(v: number | null) {
  if (!v) return '—'
  if (v >= 1e9) return `€${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `€${(v / 1e6).toFixed(1)}M`
  return `€${(v / 1e3).toFixed(0)}K`
}

function CoinRow({ coin, onSelect }: { coin: Market; onSelect: () => void }) {
  const isPositive = (coin.change_24h ?? 0) >= 0
  return (
    <tr onClick={onSelect} className="border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer transition-colors">
      <td className="py-3 px-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center text-xs font-bold">
            {coin.symbol.slice(0, 2)}
          </div>
          <div>
            <div className="font-medium text-sm">{coin.symbol}</div>
            <div className="text-xs text-gray-500">{coin.name}</div>
          </div>
        </div>
      </td>
      <td className="py-3 px-2 text-right font-mono text-sm">{formatPrice(coin.current_price)}</td>
      <td className="py-3 px-2 text-right text-sm text-gray-400 hidden md:table-cell">{formatVolume(coin.volume_24h)}</td>
      <td className="py-3 px-2 text-right">
        <span className={`inline-flex items-center gap-1 text-sm font-medium ${
          isPositive ? 'text-emerald-400' : 'text-red-400'
        }`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {Math.abs(coin.change_24h ?? 0).toFixed(2)}%
        </span>
      </td>
    </tr>
  )
}

function RecommendationCard({ rec, onSelect }: { rec: TradeRecommendation; onSelect: () => void }) {
  const isBuy = rec.recommendation === 'Strong Buy' || rec.recommendation === 'Buy'
  const borderColor = isBuy ? 'border-emerald-500/30' : rec.recommendation === 'Sell' ? 'border-red-500/30' : 'border-gray-600/30'

  return (
    <div
      onClick={onSelect}
      className={`bg-gray-900/80 border ${borderColor} rounded-xl p-4 card-hover cursor-pointer`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center text-sm font-bold">
            {rec.symbol.slice(0, 2)}
          </div>
          <div>
            <div className="font-semibold text-sm">{rec.symbol}</div>
            <div className="text-xs text-gray-500">{rec.coin_name}</div>
          </div>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          isBuy ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
        }`}>
          {rec.recommendation}
        </span>
      </div>

      <div className="flex items-center justify-between text-sm mb-2">
        <span className="text-gray-400">Score</span>
        <span className="font-mono font-bold text-cyan-400">{rec.overall_score.toFixed(0)}</span>
      </div>

      <div className="space-y-1">
        {rec.top_reasons.slice(0, 3).map((r, i) => (
          <div key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
            <span className="text-cyan-500 mt-0.5">•</span>
            {r.replace(/^[📈📊🟢💬📉🔴⏸️🌊⚖️✅⚠️]+\s*/, '')}
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between text-xs">
        <span className={`px-2 py-0.5 rounded-full ${
          rec.risk_level === 'Low' ? 'bg-emerald-500/10 text-emerald-400' :
          rec.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-400' :
          'bg-red-500/10 text-red-400'
        }`}>
          {rec.risk_level}
        </span>
        <span className="text-gray-500">
          Ziel: €{rec.target_price.toFixed(rec.target_price > 1 ? 2 : 6)}
        </span>
      </div>
    </div>
  )
}

export default function Dashboard({
  onSelectCoin,
  showAll,
}: {
  onSelectCoin: (s: string) => void
  showAll?: boolean
}) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    refetchInterval: 30000,
  })

  const { data: recs } = useQuery({
    queryKey: ['recommendations', 100],
    queryFn: () => import('../../services/api').then(m => m.getRecommendation(100, 'balanced')),
    refetchInterval: 60000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
      </div>
    )
  }

  const markets = data?.market_overview ?? []
  const aiStatus = data?.ai_status

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
            <Wallet className="w-3.5 h-3.5" /> Portfolio
          </div>
          <div className="text-xl font-bold text-emerald-400">
            €{data?.portfolio.total_value.toLocaleString('de-DE', { minimumFractionDigits: 2 }) ?? '0'}
          </div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
            <TrendingUp className="w-3.5 h-3.5" /> Trades
          </div>
          <div className="text-xl font-bold">
            {data?.total_paper_trades ?? 0}
            <span className="text-sm text-gray-400 ml-2">
              ({(data?.paper_trade_win_rate ?? 0).toFixed(0)}% Win)
            </span>
          </div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
            <Cpu className="w-3.5 h-3.5" /> KI-Status
          </div>
          <div className={`text-lg font-bold ${
            aiStatus?.status === 'warning' ? 'text-amber-400' :
            aiStatus?.status === 'cautious' ? 'text-red-400' : 'text-emerald-400'
          }`}>
            {aiStatus?.status === 'warning' ? 'Vorsichtig' :
             aiStatus?.status === 'cautious' ? 'Kritisch' : 'Aktiv'}
          </div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
            <Newspaper className="w-3.5 h-3.5" /> Vertrauen
          </div>
          <div className="text-xl font-bold text-purple-400">
            {((aiStatus?.confidence ?? 0) * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* AI Message */}
      {aiStatus?.status !== 'active' && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${
          aiStatus?.status === 'warning' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
          'bg-red-500/10 text-red-400 border border-red-500/20'
        }`}>
          {aiStatus?.message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market List */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              {showAll ? 'Alle Märkte' : 'Top-Märkte'}
            </h2>
            <button onClick={() => refetch()} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-500">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-gray-800">
                  <th className="text-left py-3 px-2 font-medium">Coin</th>
                  <th className="text-right py-3 px-2 font-medium">Preis</th>
                  <th className="text-right py-3 px-2 font-medium hidden md:table-cell">Volumen</th>
                  <th className="text-right py-3 px-2 font-medium">24h</th>
                </tr>
              </thead>
              <tbody>
                {(showAll ? markets : markets.slice(0, 10)).map((coin) => (
                  <CoinRow key={coin.symbol} coin={coin} onSelect={() => onSelectCoin(coin.symbol)} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recommendations */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            KI-Empfehlungen
          </h2>
          {recs?.slice(0, 5).map((rec) => (
            <RecommendationCard key={rec.symbol} rec={rec} onSelect={() => onSelectCoin(rec.symbol)} />
          ))}
          {(!recs || recs.length === 0) && (
            <div className="text-center py-8 text-gray-500 text-sm">
              Keine Empfehlungen verfügbar. Marktdaten werden geladen...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
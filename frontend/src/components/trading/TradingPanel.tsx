import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPaperTrades, openPaperTrade, closePaperTrade, getPaperPerformance, getPortfolio, getRecommendation, getMarkets } from '../../services/api'
import { useState } from 'react'
import { Wallet, TrendingUp, TrendingDown, Plus, X, RefreshCw, DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react'

export default function TradingPanel({
  onSelectCoin,
  showPortfolio,
}: {
  onSelectCoin: (s: string) => void
  showPortfolio?: boolean
}) {
  const queryClient = useQueryClient()
  const [showOpenTrade, setShowOpenTrade] = useState(false)
  const [tradeSymbol, setTradeSymbol] = useState('')
  const [tradeAmount, setTradeAmount] = useState('100')

  const { data: performance } = useQuery({
    queryKey: ['paper-performance'],
    queryFn: getPaperPerformance,
    refetchInterval: 15000,
  })

  const { data: portfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 15000,
  })

  const { data: trades, isLoading } = useQuery({
    queryKey: ['paper-trades', 'open'],
    queryFn: () => getPaperTrades('all', 20),
    refetchInterval: 15000,
  })

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', 100],
    queryFn: () => getRecommendation(100, 'balanced'),
    refetchInterval: 60000,
  })

  const openTradeMutation = useMutation({
    mutationFn: () => openPaperTrade(tradeSymbol.toUpperCase(), parseFloat(tradeAmount)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paper-trades'] })
      queryClient.invalidateQueries({ queryKey: ['paper-performance'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setShowOpenTrade(false)
      setTradeSymbol('')
      setTradeAmount('100')
    },
  })

  const closeTradeMutation = useMutation({
    mutationFn: (id: number) => closePaperTrade(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paper-trades'] })
      queryClient.invalidateQueries({ queryKey: ['paper-performance'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
  })

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Portfolio</div>
          <div className="text-xl font-bold text-emerald-400">€{portfolio?.total_value.toFixed(2) ?? '0'}</div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Gewinn/Verlust</div>
          <div className={`text-xl font-bold ${(performance?.total_profit_loss ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            €{performance?.total_profit_loss.toFixed(2) ?? '0'}
          </div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Win Rate</div>
          <div className="text-xl font-bold text-purple-400">{performance?.win_rate.toFixed(1) ?? '0'}%</div>
        </div>
        <div className="bg-gray-900/80 rounded-xl p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">Offene Trades</div>
          <div className="text-xl font-bold">{performance?.open_positions ?? 0}</div>
        </div>
      </div>

      {/* Trade Buttons */}
      <div className="flex gap-3">
        <button
          onClick={() => setShowOpenTrade(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg hover:bg-cyan-500/20 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" /> Neuer Trade
        </button>
      </div>

      {/* New Trade Modal */}
      {showOpenTrade && (
        <div className="bg-gray-900 rounded-xl border border-gray-700 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Neuen Paper Trade eröffnen</h3>
            <button onClick={() => setShowOpenTrade(false)} className="text-gray-500 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Coin</label>
              <input
                value={tradeSymbol}
                onChange={(e) => setTradeSymbol(e.target.value.toUpperCase())}
                placeholder="z.B. BTC"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Betrag (€)</label>
              <input
                type="number"
                value={tradeAmount}
                onChange={(e) => setTradeAmount(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
          {openTradeMutation.isPending ? (
            <button disabled className="w-full py-2.5 bg-gray-700 text-gray-400 rounded-lg text-sm">
              Wird ausgeführt...
            </button>
          ) : (
            <button
              onClick={() => openTradeMutation.mutate()}
              disabled={!tradeSymbol}
              className="w-full py-2.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg hover:bg-cyan-500/20 transition-colors text-sm"
            >
              Trade eröffnen (KI-entschieden)
            </button>
          )}
          {openTradeMutation.isError && (
            <div className="text-red-400 text-xs">Fehler: {(openTradeMutation.error as Error).message}</div>
          )}

          {/* Quick select from recommendations */}
          {recommendations && recommendations.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-2">Empfohlene Coins:</div>
              <div className="flex flex-wrap gap-2">
                {recommendations.slice(0, 5).map(r => (
                  <button
                    key={r.symbol}
                    onClick={() => setTradeSymbol(r.symbol)}
                    className={`px-3 py-1 rounded-lg text-xs border transition-colors ${
                      tradeSymbol === r.symbol
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                    }`}
                  >
                    {r.symbol}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Open Positions */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Offene Positionen</h2>
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-500 uppercase border-b border-gray-800">
                <th className="text-left py-3 px-3 font-medium">Coin</th>
                <th className="text-right py-3 px-3 font-medium">Einstieg</th>
                <th className="text-right py-3 px-3 font-medium">Menge</th>
                <th className="text-right py-3 px-3 font-medium">Wert</th>
                <th className="text-right py-3 px-3 font-medium">Aktion</th>
              </tr>
            </thead>
            <tbody>
              {portfolio?.holdings?.length > 0 ? (
                portfolio.holdings.map((h: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-3 px-3 font-medium text-sm">{h.symbol}</td>
                    <td className="py-3 px-3 text-right font-mono text-sm">€{h.entry_price.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right font-mono text-sm">{h.quantity.toFixed(6)}</td>
                    <td className={`py-3 px-3 text-right font-mono text-sm ${h.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      €{h.pnl.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => closeTradeMutation.mutate(h.id || i)}
                        className="text-xs px-2 py-1 bg-red-500/10 text-red-400 rounded hover:bg-red-500/20"
                      >
                        Schließen
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={5} className="py-8 text-center text-gray-500 text-sm">Keine offenen Positionen</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Trades */}
      {!showPortfolio && (
        <div>
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Letzte Trades</h2>
          <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-gray-800">
                  <th className="text-left py-3 px-3 font-medium">Coin</th>
                  <th className="text-right py-3 px-3 font-medium">Einstieg</th>
                  <th className="text-right py-3 px-3 font-medium">Ausstieg</th>
                  <th className="text-right py-3 px-3 font-medium">PnL</th>
                  <th className="text-right py-3 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {trades?.slice(0, 10).map((t) => (
                  <tr key={t.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer" onClick={() => onSelectCoin(t.symbol)}>
                    <td className="py-3 px-3 font-medium text-sm">{t.symbol}</td>
                    <td className="py-3 px-3 text-right font-mono text-sm">€{t.entry_price.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right font-mono text-sm">
                      {t.exit_price ? `€${t.exit_price.toFixed(2)}` : '—'}
                    </td>
                    <td className={`py-3 px-3 text-right font-mono text-sm ${
                      (t.profit_loss ?? 0) > 0 ? 'text-emerald-400' :
                      (t.profit_loss ?? 0) < 0 ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {t.profit_loss ? `€${t.profit_loss.toFixed(2)}` : '—'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        t.is_open ? 'bg-cyan-500/10 text-cyan-400' :
                        t.is_winner ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                      }`}>
                        {t.is_open ? 'Offen' : t.is_winner ? 'Gewinn' : 'Verlust'}
                      </span>
                    </td>
                  </tr>
                ))}
                {(!trades || trades.length === 0) && (
                  <tr><td colSpan={5} className="py-8 text-center text-gray-500 text-sm">Noch keine Trades</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
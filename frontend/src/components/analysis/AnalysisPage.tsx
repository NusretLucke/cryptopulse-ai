import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getRecommendation, getTechnicalAnalysis, getMarkets, getQuickAnalysis } from '../../services/api'
import { Search, TrendingUp, TrendingDown, BarChart3, Activity, ArrowRight } from 'lucide-react'

export default function AnalysisPage({ onSelectCoin }: { onSelectCoin: (s: string) => void }) {
  const [searchSymbol, setSearchSymbol] = useState('')
  const [analyzedSymbol, setAnalyzedSymbol] = useState('')
  const [investmentAmount, setInvestmentAmount] = useState('100')
  const [riskProfile, setRiskProfile] = useState('balanced')

  const { data: recommendations, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', investmentAmount, riskProfile],
    queryFn: () => getRecommendation(parseFloat(investmentAmount), riskProfile),
    refetchInterval: 60000,
  })

  const { data: quickAnalysis, isLoading: quickLoading } = useQuery({
    queryKey: ['quick-analysis', analyzedSymbol, investmentAmount],
    queryFn: () => getQuickAnalysis(analyzedSymbol, parseFloat(investmentAmount)),
    enabled: analyzedSymbol !== '',
    refetchInterval: 30000,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchSymbol.trim()) {
      setAnalyzedSymbol(searchSymbol.toUpperCase().trim())
    }
  }

  return (
    <div className="space-y-6">
      {/* KI-Assistent: 'Ich habe X Euro' */}
      <div className="bg-gradient-to-r from-cyan-500/5 to-purple-500/5 rounded-xl border border-cyan-500/10 p-5">
        <h2 className="text-lg font-semibold mb-1">KI-Assistent</h2>
        <p className="text-sm text-gray-400 mb-4">
          Gib einen Betrag ein und die KI analysiert den Markt für dich.
        </p>

        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Ich habe</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">€</span>
              <input
                type="number"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(e.target.value)}
                className="w-28 bg-gray-800 border border-gray-700 rounded-lg pl-7 pr-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Risiko</label>
            <select
              value={riskProfile}
              onChange={(e) => setRiskProfile(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
            >
              <option value="conservative">Konservativ</option>
              <option value="balanced">Ausgewogen</option>
              <option value="aggressive">Aggressiv</option>
            </select>
          </div>
          <div className="text-xs text-gray-500 py-2">
            {recsLoading ? 'Analysiere...' : `Empfehlungen: ${recommendations?.length ?? 0}`}
          </div>
        </div>
      </div>

      {/* Recommendations from KI */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
          KI-Empfehlungen für €{parseFloat(investmentAmount).toFixed(0)}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations?.map((rec) => (
            <div
              key={rec.symbol}
              onClick={() => onSelectCoin(rec.symbol)}
              className="bg-gray-900/80 border border-gray-800 rounded-xl p-4 card-hover cursor-pointer"
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
                  rec.recommendation.includes('Buy') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-700/50 text-gray-400'
                }`}>
                  {rec.recommendation}
                </span>
              </div>

              <div className="flex items-center justify-between text-sm mb-3">
                <span className="text-gray-400">Score</span>
                <span className="font-bold font-mono text-cyan-400">{rec.overall_score.toFixed(0)}</span>
              </div>

              {/* Details grid */}
              <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                <div className="bg-gray-800/50 rounded p-2">
                  <div className="text-gray-500">Einstieg</div>
                  <div className="font-mono">€{rec.current_price.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800/50 rounded p-2">
                  <div className="text-gray-500">Ziel</div>
                  <div className="font-mono text-emerald-400">€{rec.target_price.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800/50 rounded p-2">
                  <div className="text-gray-500">Stop-Loss</div>
                  <div className="font-mono text-red-400">€{rec.stop_loss.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800/50 rounded p-2">
                  <div className="text-gray-500">Erwartung</div>
                  <div className={`font-mono ${rec.expected_move_direction === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {rec.expected_move_pct > 0 ? '+' : ''}{rec.expected_move_pct.toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                {rec.top_reasons.slice(0, 3).map((r, i) => (
                  <div key={i} className="text-xs text-gray-400 flex gap-1.5">
                    <span className="text-cyan-500">•</span>
                    {r.replace(/^[^\w]+/, '').slice(0, 60)}
                  </div>
                ))}
              </div>

              <div className="mt-2 pt-2 border-t border-gray-800 flex justify-between text-xs">
                <span className={`px-1.5 py-0.5 rounded ${
                  rec.risk_level === 'Low' ? 'bg-emerald-500/10 text-emerald-400' :
                  rec.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'
                }`}>{rec.risk_level}</span>
                <span className="text-gray-500">
                  Konfidenz: {(rec.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
          {(!recommendations || recommendations.length === 0) && (
            <div className="col-span-full text-center py-8 text-gray-500 text-sm">
              Keine Empfehlungen verfügbar. Stelle sicher, dass Marktdaten geladen sind.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
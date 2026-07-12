import { useQuery } from '@tanstack/react-query'
import { getTechnicalAnalysis, getQuickAnalysis, getMarkets } from '../../services/api'
import { ArrowLeft, TrendingUp, TrendingDown, Activity, AlertTriangle, Target } from 'lucide-react'

function ScoreBar({ label, value, color = 'cyan' }: { label: string; value: number; color?: string }) {
  const barColor = value >= 70 ? 'bg-emerald-500' : value >= 45 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400 w-24 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className="font-mono w-8 text-right text-xs">{value.toFixed(0)}</span>
    </div>
  )
}

export default function MarketDetail({
  symbol,
  onBack,
}: {
  symbol: string
  onBack: () => void
}) {
  const { data: tech, isLoading: techLoading } = useQuery({
    queryKey: ['technical', symbol],
    queryFn: () => getTechnicalAnalysis(symbol),
    refetchInterval: 30000,
  })

  const { data: analysis } = useQuery({
    queryKey: ['quick-analysis', symbol],
    queryFn: () => getQuickAnalysis(symbol),
    refetchInterval: 60000,
  })

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button onClick={onBack} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm">
        <ArrowLeft className="w-4 h-4" /> Zurück
      </button>

      {/* Coin Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center text-lg font-bold">
            {symbol.slice(0, 2)}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{symbol}</h1>
            {tech && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">€{tech.current_price.toLocaleString('de-DE', { minimumFractionDigits: 2 })}</span>
                <span className={`text-sm flex items-center gap-1 ${
                  tech.trend === 'bullish' ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {tech.trend === 'bullish' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {tech.trend === 'bullish' ? 'Aufwärtstrend' : tech.trend === 'bearish' ? 'Abwärtstrend' : 'Seitwärts'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Recommendation badge */}
        {analysis && (
          <div className={`px-4 py-2 rounded-xl border text-center ${
            analysis.recommendation.includes('Buy') ? 'border-emerald-500/30 bg-emerald-500/10' :
            analysis.recommendation.includes('Sell') ? 'border-red-500/30 bg-red-500/10' :
            'border-gray-600/30 bg-gray-800/30'
          }`}>
            <div className={`text-lg font-bold ${
              analysis.recommendation.includes('Buy') ? 'text-emerald-400' :
              analysis.recommendation.includes('Sell') ? 'text-red-400' : 'text-gray-300'
            }`}>
              {analysis.recommendation}
            </div>
            <div className="text-xs text-gray-500">Konfidenz: {(analysis.confidence * 100).toFixed(0)}%</div>
          </div>
        )}
      </div>

      {techLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500" />
        </div>
      ) : tech ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Technical Indicators */}
          <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> Technische Indikatoren
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">RSI (14)</div>
                <div className={`text-lg font-bold font-mono ${
                  tech.rsi > 70 ? 'text-red-400' : tech.rsi < 30 ? 'text-emerald-400' : 'text-gray-200'
                }`}>
                  {tech.rsi.toFixed(1)}
                </div>
                <div className="text-xs text-gray-500 capitalize">{tech.rsi_signal}</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">MACD</div>
                <div className={`text-lg font-bold font-mono ${
                  tech.macd.cross === 'bullish' ? 'text-emerald-400' :
                  tech.macd.cross === 'bearish' ? 'text-red-400' : 'text-gray-200'
                }`}>
                  {tech.macd.macd.toFixed(4)}
                </div>
                <div className="text-xs text-gray-500 capitalize">{tech.macd.cross || 'neutral'}</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">Volatilität</div>
                <div className="text-lg font-bold font-mono text-purple-400 capitalize">{tech.volatility}</div>
                <div className="text-xs text-gray-500">BB Breite: {tech.bb_width.toFixed(1)}%</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">Trend</div>
                <div className={`text-lg font-bold font-mono capitalize ${
                  tech.trend === 'bullish' ? 'text-emerald-400' :
                  tech.trend === 'bearish' ? 'text-red-400' : 'text-gray-200'
                }`}>{tech.trend}</div>
                <div className="text-xs text-gray-500 capitalize">Stärke: {tech.trend_strength || tech.volume_analysis}</div>
              </div>
            </div>

            {/* EMA Signal */}
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-2">EMA Signal</div>
              <div className="flex items-center gap-4 text-sm">
                <span>EMA 12: <span className="font-mono">€{tech.ema_signals.ema_12.toFixed(2)}</span></span>
                <span>EMA 26: <span className="font-mono">€{tech.ema_signals.ema_26.toFixed(2)}</span></span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  tech.ema_signals.signal === 'bullish' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {tech.ema_signals.signal === 'bullish' ? 'Bullish' : 'Bearish'}
                </span>
              </div>
            </div>
          </div>

          {/* Support & Resistance + Scores */}
          <div className="space-y-4">
            {/* S/R Levels */}
            <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-400" /> Unterstützungen & Widerstände
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-emerald-400 mb-2">Unterstützungen</div>
                  {tech.supports.map((s, i) => (
                    <div key={i} className="text-sm font-mono text-gray-300 py-1">
                      €{s.toLocaleString('de-DE', { minimumFractionDigits: 4 })}
                    </div>
                  ))}
                  {tech.supports.length === 0 && <div className="text-xs text-gray-500">—</div>}
                </div>
                <div>
                  <div className="text-xs text-red-400 mb-2">Widerstände</div>
                  {tech.resistances.map((r, i) => (
                    <div key={i} className="text-sm font-mono text-gray-300 py-1">
                      €{r.toLocaleString('de-DE', { minimumFractionDigits: 4 })}
                    </div>
                  ))}
                  {tech.resistances.length === 0 && <div className="text-xs text-gray-500">—</div>}
                </div>
              </div>
            </div>

            {/* Overall Scores */}
            {analysis && (
              <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Bewertung</h3>
                <div className="space-y-2.5">
                  <ScoreBar label="Gesamt" value={analysis.overall_score} />
                  <ScoreBar label="Technik" value={analysis.technical_score} />
                  <ScoreBar label="Sentiment" value={analysis.sentiment_score} />
                  <ScoreBar label="Markt" value={analysis.market_score} />
                  <ScoreBar label="Risiko" value={100 - analysis.risk_score * 100} color="red" />
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* AI Reasoning / Top Reasons */}
      {analysis && analysis.top_reasons.length > 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> KI-Begründung
          </h3>
          <div className="space-y-2">
            {analysis.top_reasons.map((r, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-cyan-400 mt-0.5">•</span>
                {r}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
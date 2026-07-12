// API-Typdefinitionen für CryptoPulse AI

export interface Market {
  id: number
  symbol: string
  name: string
  current_price: number | null
  volume_24h: number | null
  market_cap: number | null
  change_24h: number | null
  high_24h: number | null
  low_24h: number | null
  last_updated: string | null
}

export interface MarketListResponse {
  markets: Market[]
  total: number
}

export interface OHLCVPoint {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  rsi: number | null
  macd: number | null
}

export interface TradeRecommendation {
  symbol: string
  coin_name: string
  current_price: number
  investment_amount: number
  quantity: number
  recommendation: string
  confidence: number
  risk_level: string
  expected_move_pct: number
  expected_move_direction: string
  top_reasons: string[]
  target_price: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  overall_score: number
  technical_score: number
  sentiment_score: number
  market_score: number
  risk_score: number
  market_phase: string
  trend_strength: string
}

export interface TechnicalAnalysis {
  symbol: string
  current_price: number
  rsi: number
  rsi_signal: string
  macd: { macd: number; signal: number; histogram: number; cross: string }
  ema_signals: { ema_12: number; ema_26: number; signal: string }
  bb_position: string
  bb_width: number
  supports: number[]
  resistances: number[]
  trend: string
  volume_analysis: string
  volatility: string
}

export interface PaperTrade {
  id?: number
  symbol: string
  entry_price: number
  amount: number
  quantity: number
  entry_time: string
  exit_price: number | null
  profit_loss: number | null
  profit_loss_pct: number | null
  is_open: boolean
  is_winner: boolean | null
  strategy_name: string
}

export interface PaperTradeResult {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_profit_loss: number
  avg_profit_per_trade: number
  open_positions: number
}

export interface PortfolioSummary {
  total_value: number
  cash_balance: number
  holdings: any[]
  performance_24h: number
  performance_7d: number
}

export interface NewsArticle {
  source: string
  title: string
  url: string
  sentiment_score: number
  sentiment_label: string
  impact_score: number
  published_at: string | null
  relevant_coins: string[]
  categories: string[]
}

export interface AIStatus {
  status: string
  accuracy: number
  total_decisions: number
  win_rate: number
  market_regime: string
  confidence: number
  message: string
  feature_weights: Record<string, number>
}

export interface DashboardData {
  market_overview: Market[]
  top_recommendations: TradeRecommendation[]
  portfolio: PortfolioSummary
  ai_status: AIStatus
  recent_news: NewsArticle[]
  total_paper_trades: number
  paper_trade_win_rate: number
}

export interface RiskAssessment {
  symbol: string
  is_safe: boolean
  risk_level: string
  max_position_size: number
  stop_loss_recommended: number
  take_profit_recommended: number
  reasons: string[]
  warnings: string[]
}
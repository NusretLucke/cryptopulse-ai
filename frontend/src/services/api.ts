// API Service Layer
import type {
  MarketListResponse,
  TradeRecommendation,
  DashboardData,
  TechnicalAnalysis,
  PaperTradeResult,
  PaperTrade,
  PortfolioSummary,
  AIStatus,
  NewsArticle,
  RiskAssessment,
  Market,
  OHLCVPoint,
} from '../types/api'

const BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000/api'
  : 'https://cryptopulse-ai.onrender.com/api'

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API Error ${res.status}: ${text}`)
  }
  return res.json()
}

// Market
export const getMarkets = (limit = 20) =>
  fetchAPI<MarketListResponse>(`/market/overview?limit=${limit}`)

export const getMarketDetail = (symbol: string) =>
  fetchAPI<Market>(`/market/${symbol}`)

export const getOHLCV = (symbol: string, limit = 100) =>
  fetchAPI<OHLCVPoint[]>(`/market/${symbol}/ohlcv?limit=${limit}`)

export const refreshMarkets = () =>
  fetchAPI<{ message: string }>('/market/refresh', { method: 'POST' })

// Analysis
export const getTechnicalAnalysis = (symbol: string) =>
  fetchAPI<TechnicalAnalysis>(`/analysis/technical/${symbol}`)

export const getRecommendation = (amount = 100, risk = 'balanced') =>
  fetchAPI<TradeRecommendation[]>(
    `/analysis/recommendation?amount=${amount}&risk=${risk}`
  )

export const getQuickAnalysis = (symbol: string, amount = 100) =>
  fetchAPI<TradeRecommendation>(`/analysis/quick?symbol=${symbol}&amount=${amount}`)

// Trading
export const getPortfolio = () =>
  fetchAPI<PortfolioSummary>('/trading/paper/portfolio')

export const getPaperPerformance = () =>
  fetchAPI<PaperTradeResult>('/trading/paper/performance')

export const getPaperTrades = (status = 'all', limit = 50) =>
  fetchAPI<PaperTrade[]>(`/trading/paper/trades?status=${status}&limit=${limit}`)

export const openPaperTrade = (symbol: string, amount = 100) =>
  fetchAPI<any>(`/trading/paper/open?symbol=${symbol}&amount=${amount}`, {
    method: 'POST',
  })

export const closePaperTrade = (tradeId: number) =>
  fetchAPI<any>(`/trading/paper/close/${tradeId}`, { method: 'POST' })

// News
export const getNews = (sentiment = 'all', limit = 20) =>
  fetchAPI<NewsArticle[]>(`/news/news?sentiment=${sentiment}&limit=${limit}`)

export const refreshNews = () =>
  fetchAPI<{ message: string }>('/news/news/refresh', { method: 'POST' })

// Risk
export const assessRisk = (symbol: string, amount = 100, portfolioValue = 10000) =>
  fetchAPI<RiskAssessment>(
    `/risk/assess?symbol=${symbol}&amount=${amount}&portfolio_value=${portfolioValue}`
  )

export const getKillSwitch = () =>
  fetchAPI<any>('/risk/kill-switch')

// Dashboard
export const getDashboard = () =>
  fetchAPI<DashboardData>('/dashboard/')

export const getAIStatus = () =>
  fetchAPI<AIStatus>('/dashboard/ai-status')

// Auth
export const register = (username: string, email: string, password: string) =>
  fetchAPI<{ access_token: string; user_id: number; username: string }>(
    '/auth/register',
    { method: 'POST', body: JSON.stringify({ username, email, password }) }
  )

export const login = (username: string, password: string) =>
  fetchAPI<{ access_token: string; user_id: number; username: string }>(
    '/auth/login',
    { method: 'POST', body: JSON.stringify({ username, password }) }
  )
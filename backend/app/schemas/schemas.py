"""Pydantic-Schemas für API Request/Response"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# ========================
# MARKT SCHEMAS
# ========================

class MarketBase(BaseModel):
    symbol: str
    name: str
    current_price: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    change_24h: Optional[float] = None


class MarketResponse(MarketBase):
    id: int
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    last_updated: Optional[datetime] = None
    price_rsi: Optional[float] = None
    trend: Optional[str] = None

    class Config:
        from_attributes = True


class MarketListResponse(BaseModel):
    markets: list[MarketResponse]
    total: int


# ========================
# OHLCV SCHEMAS
# ========================

class OHLCVResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None

    class Config:
        from_attributes = True


# ========================
# TRADING SCHEMAS
# ========================

class TradeRequest(BaseModel):
    """Anfrage: 'Ich habe 100 Euro'"""
    amount: float = Field(..., gt=0, description="Investitionsbetrag in EUR")
    strategy: Optional[str] = Field("balanced", description="Risikoprofil: conservative, balanced, aggressive")
    max_coins: Optional[int] = Field(3, ge=1, le=10)


class TradeRecommendation(BaseModel):
    """KI-Empfehlung als Antwort"""
    symbol: str
    coin_name: str
    current_price: float
    investment_amount: float
    quantity: float

    # Bewertung
    recommendation: str  # Strong Buy, Buy, Hold, Sell, Strong Sell
    confidence: float
    risk_level: str  # Low, Medium, High
    expected_move_pct: float
    expected_move_direction: str  # up, down

    # Top Gründe
    top_reasons: list[str]

    # Preisziele
    target_price: float
    stop_loss: float
    take_profit_1: float  # Erstes Ziel
    take_profit_2: float  # Zweites Ziel
    take_profit_3: float  # Drittes Ziel

    # Scores
    overall_score: float
    technical_score: float
    sentiment_score: float
    market_score: float
    risk_score: float

    # Analyse
    market_phase: str  # accumulation, markup, distribution, markdown
    trend_strength: str  # weak, moderate, strong


class PaperTradeResponse(BaseModel):
    id: Optional[int] = None
    symbol: str
    entry_price: float
    amount: float
    quantity: float
    entry_time: datetime
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    is_open: bool
    is_winner: Optional[bool] = None
    strategy_name: str

    class Config:
        from_attributes = True


class PaperTradeResult(BaseModel):
    """Zusammenfassung aller Paper Trades"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    avg_profit_per_trade: float
    open_positions: int
    best_trade: Optional[PaperTradeResponse] = None
    worst_trade: Optional[PaperTradeResponse] = None


class PortfolioSummary(BaseModel):
    total_value: float
    cash_balance: float
    holdings: list[dict]
    performance_24h: float
    performance_7d: float


# ========================
# ANALYSE SCHEMAS
# ========================

class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    rsi: float
    rsi_signal: str  # overbought, oversold, neutral
    macd: dict
    ema_signals: dict
    bb_position: str  # above_upper, inside, below_lower
    bb_width: float  # Volatilitätsindikator
    supports: list[float]
    resistances: list[float]
    trend: str  # bullish, bearish, sideways
    volume_analysis: str
    volatility: str


class NewsSentimentResponse(BaseModel):
    source: str
    title: str
    url: str
    sentiment_score: float
    sentiment_label: str
    impact_score: float
    published_at: Optional[datetime] = None
    relevant_coins: list[str]
    categories: list[str]


class SocialSentimentResponse(BaseModel):
    platform: str
    sentiment_score: float
    mention_count: int
    hype_score: float
    bot_activity_score: float
    timestamp: datetime


# ========================
# USER SCHEMAS
# ========================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class UserSettings(BaseModel):
    preferred_currency: Optional[str] = "EUR"
    risk_tolerance: Optional[str] = "medium"
    language: Optional[str] = "de"


class BinanceCredentials(BaseModel):
    api_key: str
    secret_key: str


# ========================
# KI-SELBSTKONTROLLE
# ========================

class AIStatusResponse(BaseModel):
    status: str  # active, cautious, warning
    accuracy: float
    total_decisions: int
    win_rate: float
    market_regime: str
    confidence: float
    message: str
    feature_weights: dict


# ========================
# DASHBOARD
# ========================

class DashboardResponse(BaseModel):
    market_overview: list[MarketResponse]
    top_recommendations: list[TradeRecommendation]
    portfolio: PortfolioSummary
    ai_status: AIStatusResponse
    recent_news: list[NewsSentimentResponse]
    total_paper_trades: int
    paper_trade_win_rate: float
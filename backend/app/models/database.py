"""Datenbank-Modelle für CryptoPulse AI"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SAEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()


class DecisionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TimeFrame(str, enum.Enum):
    SHORT = "1h"
    MEDIUM = "4h"
    LONG = "1d"
    WEEK = "1w"


# ========================
# MARKTDATEN
# ========================

class Market(Base):
    """Aktuelle Marktdaten pro Coin"""
    __tablename__ = "markets"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    current_price = Column(Float)
    volume_24h = Column(Float)
    market_cap = Column(Float)
    change_24h = Column(Float)
    high_24h = Column(Float)
    low_24h = Column(Float)
    circulating_supply = Column(Float)
    total_supply = Column(Float)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    ohlcv_data = relationship("OHLCV", back_populates="market", cascade="all, delete-orphan")
    onchain_metrics = relationship("OnChainMetrics", back_populates="market", uselist=False)
    social_sentiments = relationship("SocialSentiment", back_populates="market", cascade="all, delete-orphan")
    trading_decisions = relationship("TradingDecision", back_populates="market", cascade="all, delete-orphan")


class OHLCV(Base):
    """Zeitreihen-Daten (Kerzen)"""
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Technische Indikatoren (berechnet)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    atr = Column(Float)
    volume_sma = Column(Float)

    market = relationship("Market", back_populates="ohlcv_data")


# ========================
# ON-CHAIN ANALYSE
# ========================

class OnChainMetrics(Base):
    """Blockchain-Metriken"""
    __tablename__ = "onchain_metrics"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), unique=True, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    # Whale-Transaktionen
    large_transactions_24h = Column(Integer, default=0)
    whale_inflow = Column(Float, default=0.0)
    whale_outflow = Column(Float, default=0.0)

    # Exchange Flows
    exchange_netflow = Column(Float, default=0.0)
    exchange_inflow = Column(Float, default=0.0)
    exchange_outflow = Column(Float, default=0.0)

    # Holder
    total_holders = Column(Integer, default=0)
    holder_change_24h = Column(Float, default=0.0)
    concentration_ratio = Column(Float, default=0.0)  # Top 10 Holder %

    # Staking & Supply
    staking_ratio = Column(Float, default=0.0)
    supply_staked = Column(Float, default=0.0)
    next_unlock_date = Column(DateTime, nullable=True)
    unlock_amount = Column(Float, default=0.0)

    # Aktivität
    active_addresses_24h = Column(Integer, default=0)
    transaction_count_24h = Column(Integer, default=0)
    avg_transaction_value = Column(Float, default=0.0)

    market = relationship("Market", back_populates="onchain_metrics")


# ========================
# NEWS & SENTIMENT
# ========================

class NewsArticle(Base):
    """KI-analysierte Nachrichten"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    source = Column(String(100))
    title = Column(String(500))
    url = Column(String(1000), unique=True)
    content_summary = Column(Text)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=func.now())

    # KI-Analyse
    sentiment_score = Column(Float)  # -1.0 bis 1.0
    sentiment_label = Column(String(20))  # positiv, neutral, negativ
    impact_score = Column(Float)  # 0.0 bis 1.0
    relevant_coins = Column(JSON)  # Liste der erwähnten Coins
    categories = Column(JSON)  # z.B. ["regulation", "technology", "partnership"]
    is_analyzed = Column(Boolean, default=False)


class SocialSentiment(Base):
    """Social-Media-Stimmung pro Coin"""
    __tablename__ = "social_sentiment"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    platform = Column(String(50))  # twitter, reddit, telegram, discord
    timestamp = Column(DateTime, default=func.now())

    sentiment_score = Column(Float)  # -1.0 bis 1.0
    mention_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    hype_score = Column(Float)  # 0.0 bis 1.0
    bot_activity_score = Column(Float)  # 0.0 bis 1.0
    engagement_rate = Column(Float)

    market = relationship("Market", back_populates="social_sentiments")


# ========================
# TRADING & ENTSCHEIDUNGEN
# ========================

class TradingDecision(Base):
    """KI-Entscheidungen und Empfehlungen"""
    __tablename__ = "trading_decisions"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now())

    decision = Column(String(20))  # buy, sell, hold
    confidence_score = Column(Float)  # 0.0 bis 1.0
    risk_score = Column(Float)  # 0.0 (sicher) bis 1.0 (riskant)
    expected_move_pct = Column(Float)  # erwartete Bewegung in %
    expected_move_direction = Column(String(10))  # up, down
    target_price = Column(Float)
    stop_loss_price = Column(Float)

    # Multi-Faktor-Scores
    market_score = Column(Float)
    technical_score = Column(Float)
    onchain_score = Column(Float)
    news_score = Column(Float)
    sentiment_score = Column(Float)
    overall_score = Column(Float)

    # Begründung
    reasoning = Column(JSON)
    top_reasons = Column(JSON)  # Top 5 Gründe

    market = relationship("Market", back_populates="trading_decisions")


class PaperTrade(Base):
    """Simulierte Trades (Paper Trading)"""
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    symbol = Column(String(20), nullable=False)

    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    amount = Column(Float)  # Investierter Betrag in €
    quantity = Column(Float)  # Coin-Menge
    entry_time = Column(DateTime, default=func.now())
    exit_time = Column(DateTime, nullable=True)

    profit_loss = Column(Float, nullable=True)  # In €
    profit_loss_pct = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True)
    is_winner = Column(Boolean, nullable=True)

    # Strategieverfolgung
    strategy_name = Column(String(100))
    decision_id = Column(Integer, ForeignKey("trading_decisions.id"), nullable=True)

    # Stop-Loss / Take-Profit
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    stop_loss_hit = Column(Boolean, default=False)
    take_profit_hit = Column(Boolean, default=False)


# ========================
# KI-LERNEN
# ========================

class LearningLog(Base):
    """KI-Lernverlauf (Selbstkontrolle)"""
    __tablename__ = "learning_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())

    # Entscheidungsqualität
    total_decisions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)

    # Paper Trading Ergebnisse
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_profit_loss = Column(Float, default=0.0)
    avg_profit_per_trade = Column(Float, default=0.0)

    # Selbstbewertung
    model_performance_score = Column(Float)  # 0.0 - 1.0
    market_regime = Column(String(50))  # bull, bear, sideways, volatile
    is_overconfident = Column(Boolean, default=False)
    warning_message = Column(Text, nullable=True)

    # Gewichtungen (aktuell)
    feature_weights = Column(JSON)


# ========================
# USER & SICHERHEIT
# ========================

class User(Base):
    """Benutzer"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Präferenzen
    preferred_currency = Column(String(10), default="EUR")
    risk_tolerance = Column(String(20), default="medium")  # low, medium, high
    language = Column(String(10), default="de")

    # Binance API (verschlüsselt)
    binance_api_key_encrypted = Column(String(500), nullable=True)
    binance_secret_key_encrypted = Column(String(500), nullable=True)
    is_binance_connected = Column(Boolean, default=False)

    portfolio = relationship("Portfolio", uselist=False, back_populates="user")


class Portfolio(Base):
    """User-Portfolio"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="portfolio")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """Coin-Bestand im Portfolio"""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float)
    avg_entry_price = Column(Float)
    current_value = Column(Float)

    portfolio = relationship("Portfolio", back_populates="holdings")


class AuditLog(Base):
    """Sicherheits-Log"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=func.now())
    success = Column(Boolean, default=True)
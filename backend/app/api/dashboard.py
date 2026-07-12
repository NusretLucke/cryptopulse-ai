"""Dashboard - API Endpoints (Gesamtübersicht)"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.db.database import get_db
from app.models.database import Market, PaperTrade, LearningLog, NewsArticle
from app.schemas.schemas import (
    DashboardResponse, MarketResponse, PortfolioSummary,
    AIStatusResponse, NewsSentimentResponse, TradeRecommendation,
)
from app.services.ai.decision_engine import DecisionEngine, LearningSystem
from app.services.trading.paper_trading import PaperTradingEngine
from app.services.market.market_service import MarketService

router = APIRouter()
decision_engine = DecisionEngine()
learning_system = LearningSystem(decision_engine)
trading_engine = PaperTradingEngine()
market_service = MarketService()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Vollständiges Dashboard mit allen Daten"""
    # 1. Marktübersicht
    result = await db.execute(
        select(Market)
        .where(Market.current_price.isnot(None))
        .order_by(desc(Market.market_cap))
        .limit(20)
    )
    markets = result.scalars().all()

    market_responses = [
        MarketResponse(
            id=m.id, symbol=m.symbol, name=m.name,
            current_price=m.current_price, volume_24h=m.volume_24h,
            market_cap=m.market_cap, change_24h=m.change_24h,
            high_24h=m.high_24h, low_24h=m.low_24h,
            last_updated=m.last_updated,
        )
        for m in markets
    ]

    # 2. KI-Empfehlungen
    recommendations = await decision_engine.get_buy_recommendation(db)
    top_recs = []
    for rec in recommendations[:5]:
        current_price = rec.target_price / (1 + rec.expected_move_pct / 100)
        top_recs.append(TradeRecommendation(
            symbol=rec.symbol, coin_name=rec.coin_name,
            current_price=current_price,
            investment_amount=100.0,
            quantity=100.0 / current_price,
            recommendation="Strong Buy" if rec.confidence > 0.7 else "Buy",
            confidence=rec.confidence,
            risk_level="High" if rec.risk_score > 0.6
                      else "Medium" if rec.risk_score > 0.3
                      else "Low",
            expected_move_pct=rec.expected_move_pct,
            expected_move_direction=rec.expected_direction,
            top_reasons=rec.top_reasons,
            target_price=rec.target_price, stop_loss=rec.stop_loss,
            take_profit_1=rec.take_profit_1,
            take_profit_2=rec.take_profit_2,
            take_profit_3=rec.take_profit_3,
            overall_score=rec.overall_score,
            technical_score=rec.technical_score,
            sentiment_score=rec.sentiment_score,
            market_score=rec.market_score,
            risk_score=rec.risk_score,
            market_phase=rec.market_phase,
            trend_strength=rec.trend_strength,
        ))

    # 3. Portfolio
    portfolio_data = await trading_engine.get_portfolio(db)
    portfolio = PortfolioSummary(
        total_value=portfolio_data["total_value"],
        cash_balance=portfolio_data["cash"],
        holdings=portfolio_data["open_positions"],
        performance_24h=0.0, performance_7d=0.0,
    )

    # 4. KI-Status
    ai_status_data = await learning_system.self_check(db)
    ai_status = AIStatusResponse(
        status=ai_status_data["status"],
        accuracy=ai_status_data["accuracy"],
        total_decisions=ai_status_data["total_decisions"],
        win_rate=ai_status_data["win_rate"],
        market_regime=ai_status_data["market_regime"],
        confidence=ai_status_data["confidence"],
        message=ai_status_data["message"],
        feature_weights=ai_status_data["feature_weights"],
    )

    # 5. News
    news_result = await db.execute(
        select(NewsArticle)
        .order_by(desc(NewsArticle.published_at))
        .limit(5)
    )
    articles = news_result.scalars().all()
    news = [
        NewsSentimentResponse(
            source=a.source, title=a.title, url=a.url,
            sentiment_score=a.sentiment_score,
            sentiment_label=a.sentiment_label,
            impact_score=a.impact_score,
            published_at=a.published_at,
            relevant_coins=a.relevant_coins or [],
            categories=a.categories or [],
        )
        for a in articles
    ]

    # 6. Paper Trade Statistik
    perf = await trading_engine.get_performance(db)

    return DashboardResponse(
        market_overview=market_responses,
        top_recommendations=top_recs,
        portfolio=portfolio,
        ai_status=ai_status,
        recent_news=news,
        total_paper_trades=perf.total_trades,
        paper_trade_win_rate=perf.win_rate,
    )


@router.get("/ai-status", response_model=AIStatusResponse)
async def get_ai_status(db: AsyncSession = Depends(get_db)):
    """KI-Selbstkontrolle abrufen"""
    status = await learning_system.self_check(db)
    return AIStatusResponse(
        status=status["status"],
        accuracy=status["accuracy"],
        total_decisions=status["total_decisions"],
        win_rate=status["win_rate"],
        market_regime=status["market_regime"],
        confidence=status["confidence"],
        message=status["message"],
        feature_weights=status["feature_weights"],
    )
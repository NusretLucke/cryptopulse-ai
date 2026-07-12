"""Analyse-API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.database import Market, OHLCV
from app.schemas.schemas import (
    TechnicalAnalysisResponse, TradeRecommendation,
    NewsSentimentResponse, SocialSentimentResponse,
)
from app.services.analysis.technical_analysis import TechnicalAnalysisEngine
from app.services.analysis.technical_analysis import TechnicalIndicators
from app.services.market.market_service import MarketService
from app.services.ai.decision_engine import DecisionEngine

router = APIRouter()
technical_engine = TechnicalAnalysisEngine()
market_service = MarketService()
decision_engine = DecisionEngine()


@router.get("/technical/{symbol}", response_model=TechnicalAnalysisResponse)
async def get_technical_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Vollständige technische Analyse für einen Coin"""
    market = await market_service.get_market_by_symbol(db, symbol)
    if not market:
        raise HTTPException(status_code=404, detail="Coin nicht gefunden")

    ohlcv = await market_service.get_ohlcv(db, symbol, 200)
    if len(ohlcv) < 50:
        raise HTTPException(status_code=400, detail="Nicht genug Daten für Analyse")

    import pandas as pd
    df = pd.DataFrame([
        {"timestamp": r.timestamp, "open": r.open, "high": r.high,
         "low": r.low, "close": r.close, "volume": r.volume}
        for r in ohlcv
    ])

    indicators = technical_engine.analyze(df, symbol)
    if not indicators:
        raise HTTPException(status_code=500, detail="Analyse fehlgeschlagen")

    tech_score, signals = technical_engine.get_technical_score(indicators)

    return TechnicalAnalysisResponse(
        symbol=indicators.symbol,
        current_price=indicators.current_price,
        rsi=indicators.rsi,
        rsi_signal=indicators.rsi_signal,
        macd={
            "macd": round(indicators.macd, 4),
            "signal": round(indicators.macd_signal, 4),
            "histogram": round(indicators.macd_histogram, 4),
            "cross": indicators.macd_cross,
        },
        ema_signals={
            "ema_12": round(indicators.ema_12, 2),
            "ema_26": round(indicators.ema_26, 2),
            "signal": indicators.ema_signal,
        },
        bb_position=indicators.bb_position,
        bb_width=round(indicators.bb_width, 2),
        supports=[round(s, 4) for s in indicators.supports],
        resistances=[round(r, 4) for r in indicators.resistances],
        trend=indicators.trend,
        volume_analysis=indicators.volume_trend,
        volatility=indicators.volatility,
    )


@router.get("/recommendation", response_model=list[TradeRecommendation])
async def get_recommendation(
    amount: float = Query(100.0, ge=10, description="Investitionsbetrag in EUR"),
    risk: str = Query("balanced", pattern="^(conservative|balanced|aggressive)$"),
    db: AsyncSession = Depends(get_db),
):
    """KI-Empfehlung: 'Ich habe X Euro'"""
    recommendations = await decision_engine.get_buy_recommendation(
        db, amount=amount, risk_profile=risk
    )

    if not recommendations:
        raise HTTPException(status_code=404, detail="Keine Empfehlungen verfügbar")

    result = []
    for rec in recommendations[:5]:
        result.append(TradeRecommendation(
            symbol=rec.symbol,
            coin_name=rec.coin_name,
            current_price=rec.target_price / (1 + rec.expected_move_pct / 100),
            investment_amount=amount,
            quantity=amount / (rec.target_price / (1 + rec.expected_move_pct / 100)),
            recommendation="Strong Buy" if rec.decision == "buy" and rec.confidence > 0.7
                          else "Buy" if rec.decision == "buy"
                          else "Hold" if rec.decision == "hold"
                          else "Sell",
            confidence=rec.confidence,
            risk_level="High" if rec.risk_score > 0.6
                      else "Medium" if rec.risk_score > 0.3
                      else "Low",
            expected_move_pct=rec.expected_move_pct,
            expected_move_direction=rec.expected_direction,
            top_reasons=rec.top_reasons,
            target_price=rec.target_price,
            stop_loss=rec.stop_loss,
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

    return result


@router.get("/quick", response_model=TradeRecommendation)
async def quick_analysis(
    symbol: str = Query(..., description="Coin-Symbol, z.B. BTC"),
    amount: float = Query(100.0, ge=10),
    db: AsyncSession = Depends(get_db),
):
    """Schnellanalyse für einen bestimmten Coin"""
    decision = await decision_engine.analyze_coin(db, symbol, amount)
    if not decision:
        raise HTTPException(status_code=404, detail="Analyse fehlgeschlagen")

    return TradeRecommendation(
        symbol=decision.symbol,
        coin_name=decision.coin_name,
        current_price=decision.target_price / (1 + decision.expected_move_pct / 100),
        investment_amount=amount,
        quantity=amount / (decision.target_price / (1 + decision.expected_move_pct / 100)),
        recommendation="Strong Buy" if decision.decision == "buy" and decision.confidence > 0.7
                      else "Buy" if decision.decision == "buy"
                      else "Hold" if decision.decision == "hold"
                      else "Sell",
        confidence=decision.confidence,
        risk_level="High" if decision.risk_score > 0.6
                  else "Medium" if decision.risk_score > 0.3
                  else "Low",
        expected_move_pct=decision.expected_move_pct,
        expected_move_direction=decision.expected_direction,
        top_reasons=decision.top_reasons,
        target_price=decision.target_price,
        stop_loss=decision.stop_loss,
        take_profit_1=decision.take_profit_1,
        take_profit_2=decision.take_profit_2,
        take_profit_3=decision.take_profit_3,
        overall_score=decision.overall_score,
        technical_score=decision.technical_score,
        sentiment_score=decision.sentiment_score,
        market_score=decision.market_score,
        risk_score=decision.risk_score,
        market_phase=decision.market_phase,
        trend_strength=decision.trend_strength,
    )
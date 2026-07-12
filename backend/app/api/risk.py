"""Risk Management - API Endpoints"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.database import Market, PaperTrade
from app.services.risk.risk_manager import RiskManager

router = APIRouter()
risk_manager = RiskManager()


@router.get("/assess")
async def assess_trade_risk(
    symbol: str = Query(..., description="Coin-Symbol"),
    amount: float = Query(100.0, ge=10, description="Investitionsbetrag"),
    portfolio_value: float = Query(10000.0, ge=100, description="Portfoliowert in EUR"),
    db: AsyncSession = Depends(get_db),
):
    """Risikobewertung für eine geplante Investition"""
    # Coin-Daten laden
    result = await db.execute(
        select(Market).where(Market.symbol == symbol.upper())
    )
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail="Coin nicht gefunden")

    # Bestehende Positionen
    pos_result = await db.execute(
        select(PaperTrade).where(
            PaperTrade.symbol == symbol.upper(),
            PaperTrade.is_open == True,
        )
    )
    existing = [
        {"symbol": t.symbol, "value": t.quantity * (market.current_price or t.entry_price)}
        for t in pos_result.scalars().all()
    ]

    # Volatilität berechnen
    volatility = abs(market.change_24h or 0)

    # Täglicher PnL
    trade_result = await db.execute(
        select(PaperTrade).where(
            PaperTrade.is_open == False
        )
    )
    closed_trades = trade_result.scalars().all()
    daily_pnl = sum(t.profit_loss or 0 for t in closed_trades[-10:])

    assessment = risk_manager.assess_trade(
        symbol=symbol,
        amount=amount,
        portfolio_value=portfolio_value,
        coin_volatility=volatility,
        market_cap=market.market_cap or 0,
        daily_pnl=daily_pnl,
        existing_positions=existing,
    )

    return {
        "symbol": symbol,
        "is_safe": assessment.is_safe,
        "risk_level": assessment.risk_level,
        "max_position_size": round(assessment.max_position_size, 2),
        "max_position_pct": assessment.max_position_pct,
        "stop_loss_recommended": assessment.stop_loss_recommended,
        "take_profit_recommended": assessment.take_profit_recommended,
        "reasons": assessment.reasons,
        "warnings": assessment.warnings,
    }


@router.get("/scam-check")
async def check_scam(
    symbol: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Scam-Risiko für einen Coin prüfen"""
    result = await db.execute(
        select(Market).where(Market.symbol == symbol.upper())
    )
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail="Coin nicht gefunden")

    scam_check = RiskManager.check_scam_risk(
        symbol=market.symbol,
        market_cap=market.market_cap or 0,
        volume_24h=market.volume_24h or 0,
        price_change_24h=market.change_24h or 0,
        holder_count=0,
    )

    return {
        "symbol": symbol,
        **scam_check,
    }


@router.get("/kill-switch")
async def check_kill_switch(db: AsyncSession = Depends(get_db)):
    """Not-Aus-Status prüfen"""
    from datetime import datetime, timedelta
    # Trades in der letzten Stunde zählen
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(PaperTrade).where(PaperTrade.entry_time >= one_hour_ago)
    )
    recent_trades = len(result.scalars().all())

    is_triggered = RiskManager.emergency_kill_switch(recent_trades)

    return {
        "kill_switch_active": is_triggered,
        "trades_last_hour": recent_trades,
        "max_trades_per_hour": 5,
        "status": "🚨 AKTIVIERT" if is_triggered else "✅ Normal",
    }
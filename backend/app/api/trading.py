"""Trading-API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.database import PaperTrade, Market
from app.schemas.schemas import (
    TradeRecommendation, PaperTradeResponse, PaperTradeResult,
    PortfolioSummary,
)
from app.services.trading.paper_trading import PaperTradingEngine
from app.services.ai.decision_engine import DecisionEngine

router = APIRouter()
trading_engine = PaperTradingEngine()
decision_engine = DecisionEngine()


@router.get("/paper/portfolio", response_model=PortfolioSummary)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    """Portfolio-Übersicht (Paper Trading)"""
    portfolio = await trading_engine.get_portfolio(db)
    return PortfolioSummary(
        total_value=portfolio["total_value"],
        cash_balance=portfolio["cash"],
        holdings=portfolio["open_positions"],
        performance_24h=0.0,
        performance_7d=0.0,
    )


@router.get("/paper/performance", response_model=PaperTradeResult)
async def get_performance(db: AsyncSession = Depends(get_db)):
    """Paper Trading Performance"""
    return await trading_engine.get_performance(db)


@router.get("/paper/trades", response_model=list[PaperTradeResponse])
async def get_trades(
    status: str = Query("all", pattern="^(all|open|closed)$"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Alle Paper Trades abrufen"""
    from sqlalchemy import desc

    query = select(PaperTrade).order_by(desc(PaperTrade.entry_time))

    if status == "open":
        query = query.where(PaperTrade.is_open == True)
    elif status == "closed":
        query = query.where(PaperTrade.is_open == False)

    result = await db.execute(query.limit(limit))
    trades = result.scalars().all()

    return [
        PaperTradeResponse(
            id=t.id, symbol=t.symbol,
            entry_price=t.entry_price, amount=t.amount,
            quantity=t.quantity, entry_time=t.entry_time,
            exit_price=t.exit_price, profit_loss=t.profit_loss,
            profit_loss_pct=t.profit_loss_pct,
            is_open=t.is_open, is_winner=t.is_winner,
            strategy_name=t.strategy_name,
        )
        for t in trades
    ]


@router.post("/paper/open")
async def open_paper_trade(
    symbol: str = Query(..., description="Coin-Symbol"),
    amount: float = Query(100.0, ge=10, description="Betrag in EUR"),
    db: AsyncSession = Depends(get_db),
):
    """Neuen Paper Trade eröffnen (KI-entschieden)"""
    # KI-Entscheidung holen
    decision = await decision_engine.analyze_coin(db, symbol, amount)
    if not decision or decision.decision != "buy":
        raise HTTPException(
            status_code=400,
            detail=f"Keine Kaufempfehlung für {symbol}. "
                   f"Entscheidung: {decision.decision if decision else 'N/A'}"
        )

    current_price = decision.target_price / (1 + decision.expected_move_pct / 100)

    trade = await trading_engine.create_trade(
        db=db,
        symbol=symbol,
        entry_price=current_price,
        amount=amount,
        strategy="ai_decision",
        stop_loss=decision.stop_loss,
        take_profit=decision.target_price,
    )

    return {
        "message": f"✅ Paper Trade eröffnet: {amount}€ in {symbol}",
        "trade": PaperTradeResponse(
            id=trade.id, symbol=trade.symbol,
            entry_price=trade.entry_price, amount=trade.amount,
            quantity=trade.quantity, entry_time=trade.entry_time,
            is_open=True, strategy_name=trade.strategy_name,
        ),
        "decision": {
            "confidence": decision.confidence,
            "risk_score": decision.risk_score,
            "target": decision.target_price,
            "stop_loss": decision.stop_loss,
            "top_reasons": decision.top_reasons[:3],
        },
    }


@router.post("/paper/close/{trade_id}")
async def close_paper_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Paper Trade manuell schließen"""
    # Aktuellen Preis holen
    trade_result = await db.execute(
        select(PaperTrade).where(PaperTrade.id == trade_id)
    )
    trade = trade_result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade nicht gefunden")

    market_result = await db.execute(
        select(Market).where(Market.symbol == trade.symbol)
    )
    market = market_result.scalar_one_or_none()
    if not market:
        raise HTTPException(
            status_code=404, detail="Coin nicht gefunden"
        )

    closed = await trading_engine.close_trade(db, trade_id, market.current_price)
    if not closed:
        raise HTTPException(status_code=400, detail="Trade bereits geschlossen")

    return {
        "message": f"Trade geschlossen: {closed.symbol}",
        "profit_loss": closed.profit_loss,
        "profit_loss_pct": closed.profit_loss_pct,
        "is_winner": closed.is_winner,
    }


@router.get("/paper/update")
async def update_trades(db: AsyncSession = Depends(get_db)):
    """Offene Trades aktualisieren (Stop-Loss/Take-Profit)"""
    await trading_engine.update_open_trades(db)
    return {"message": "Trades aktualisiert"}
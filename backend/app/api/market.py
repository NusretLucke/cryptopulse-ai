"""Market Data - API Endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.models.database import Market, OHLCV
from app.schemas.schemas import MarketResponse, MarketListResponse, OHLCVResponse
from app.services.market.market_service import MarketService

router = APIRouter()
market_service = MarketService()


@router.get("/overview", response_model=MarketListResponse)
async def get_market_overview(
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("market_cap", pattern="^(market_cap|volume_24h|change_24h)$"),
    db: AsyncSession = Depends(get_db),
):
    """Marktübersicht aller Top-Coins"""
    order_col = getattr(Market, sort_by, Market.market_cap)
    result = await db.execute(
        select(Market).order_by(desc(order_col)).limit(limit)
    )
    markets = result.scalars().all()

    market_responses = []
    for m in markets:
        market_responses.append(MarketResponse(
            id=m.id, symbol=m.symbol, name=m.name,
            current_price=m.current_price,
            volume_24h=m.volume_24h,
            market_cap=m.market_cap,
            change_24h=m.change_24h,
            high_24h=m.high_24h,
            low_24h=m.low_24h,
            last_updated=m.last_updated,
        ))

    return MarketListResponse(markets=market_responses, total=len(markets))


@router.get("/{symbol}", response_model=MarketResponse)
async def get_market_detail(symbol: str, db: AsyncSession = Depends(get_db)):
    """Details zu einem Coin"""
    result = await db.execute(
        select(Market).where(Market.symbol == symbol.upper())
    )
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail="Coin nicht gefunden")

    return MarketResponse(
        id=market.id, symbol=market.symbol, name=market.name,
        current_price=market.current_price,
        volume_24h=market.volume_24h,
        market_cap=market.market_cap,
        change_24h=market.change_24h,
        high_24h=market.high_24h,
        low_24h=market.low_24h,
        last_updated=market.last_updated,
    )


@router.get("/{symbol}/ohlcv", response_model=list[OHLCVResponse])
async def get_ohlcv_data(
    symbol: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """OHLCV-Verlaufsdaten + Indikatoren"""
    ohlcv_data = await market_service.get_ohlcv(db, symbol, limit)
    if not ohlcv_data:
        raise HTTPException(status_code=404, detail="Keine Daten gefunden")

    return [
        OHLCVResponse(
            timestamp=o.timestamp, open=o.open, high=o.high,
            low=o.low, close=o.close, volume=o.volume,
            rsi=o.rsi, macd=o.macd, ema_12=o.ema_12, ema_26=o.ema_26,
            bb_upper=o.bb_upper, bb_lower=o.bb_lower,
        )
        for o in ohlcv_data
    ]


@router.post("/refresh")
async def refresh_market_data(db: AsyncSession = Depends(get_db)):
    """Marktdaten aktualisieren (Live-Kurse + OHLCV + KI-Analyse)"""
    await market_service.update_market(db)
    # Auch OHLCV nachladen für bessere Analyse
    await market_service.update_ohlcv(db, days=7)
    return {"message": "Marktdaten + OHLCV aktualisiert (CoinCap live)"}


@router.get("/search", response_model=list[dict])
async def search_coins(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Coins suchen"""
    result = await db.execute(
        select(Market).where(
            Market.symbol.ilike(f"%{query}%") | Market.name.ilike(f"%{query}%")
        ).limit(10)
    )
    coins = result.scalars().all()
    return [
        {"symbol": c.symbol, "name": c.name, "price": c.current_price}
        for c in coins
    ]
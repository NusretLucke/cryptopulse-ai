"""Seed-Script: Erzeugt OHLCV-Daten für Demo-Zwecke (falls CoinGecko ratelimitiert ist)"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.models.database import Market, OHLCV
from app.db.database import async_session_factory, init_db
from datetime import datetime, timedelta
import random
import math


def generate_ohlcv(base_price: float, days: int = 60, seed: int = 42, trend_bias: str = "random") -> list[dict]:
    """Realistische OHLCV-Kerzen mit verschiedenen Marktphasen"""
    random.seed(seed)
    data = []
    price = base_price

    # Marktphase bestimmen
    if trend_bias == "random":
        phases = ["bullish", "bearish", "sideways", "volatile"]
        trend_bias = phases[seed % len(phases)]

    for i in range(days):
        # Simuliere 4h-Kerzen (6 pro Tag)
        for h in range(6):
            timestamp = datetime.utcnow() - timedelta(days=days - i) + timedelta(hours=h * 4)

            # Drift und Volatilität basierend auf Marktphase
            if trend_bias == "bullish":
                drift = 0.0008  # Starker Aufwärtstrend
                volatility = 0.025
            elif trend_bias == "bearish":
                drift = -0.0006  # Abwärtstrend
                volatility = 0.03
            elif trend_bias == "volatile":
                drift = 0.0
                volatility = 0.05  # Hohe Volatilität
            else:  # sideways
                drift = 0.00005
                volatility = 0.015

            # Regime-Shift: Alle ~10 Tage kann sich der Trend ändern
            if i > 0 and i % 10 == 0 and h == 0:
                if random.random() < 0.2:  # 20% Chance auf Trendwechsel
                    drift = -drift

            shock = random.gauss(drift, volatility)
            price *= (1 + shock)
            price = max(price, base_price * 0.1)  # Nicht unter 10% des Basispreises

            # Kerze generieren
            open_p = price * (1 + random.gauss(0, 0.003))
            close_p = price * (1 + random.gauss(0, 0.003))
            high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 0.008)))
            low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 0.008)))
            volume = random.uniform(1e6, 1e9) * (1 + abs(shock) * 15)

            # Volumen steigt bei großen Bewegungen
            if abs(shock) > 0.03:
                volume *= 1.5

            data.append({
                "timestamp": timestamp,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": round(volume, 2),
            })

    return data


async def seed_data():
    await init_db()
    async with async_session_factory() as db:
        # Vorhandene Märkte abrufen
        from sqlalchemy import select
        result = await db.execute(select(Market))
        markets = result.scalars().all()

        if not markets:
            print("⚠️ Keine Märkte in DB. Bitte erst /api/market/refresh aufrufen.")
            return

        for market in markets:
            # Prüfen ob bereits OHLCV-Daten existieren
            result = await db.execute(
                select(OHLCV).where(OHLCV.market_id == market.id).limit(1)
            )
            if result.scalar_one_or_none():
                print(f"  ⏭️  {market.symbol}: OHLCV-Daten bereits vorhanden")
                continue

            # Bestehenden Preis als Basis nehmen oder Fallback
            base = market.current_price or (
                50000 if market.symbol == "BTC" else
                1500 if market.symbol == "ETH" else
                1.0 if market.symbol in ("USDT", "USDC") else
                50
            )

            # Marktphase für realistische Signale zuweisen
            phase_map = {
                "BTC": "bullish", "ETH": "bullish", "SOL": "bullish",
                "XRP": "bullish", "ADA": "bullish", "LINK": "bullish",
                "AVAX": "bullish", "DOT": "sideways", "DOGE": "volatile",
                "MATIC": "bearish", "ATOM": "bearish", "NEAR": "bullish",
                "OP": "sideways", "ARB": "bearish", "APT": "bullish",
                "SUI": "bullish", "TIA": "volatile", "SEI": "volatile",
            }
            trend_bias = phase_map.get(market.symbol, "random")

            data = generate_ohlcv(base, days=60, seed=hash(market.symbol) % 1000, trend_bias=trend_bias)

            for point in data:
                ohlcv = OHLCV(
                    market_id=market.id,
                    timestamp=point["timestamp"],
                    open=point["open"],
                    high=point["high"],
                    low=point["low"],
                    close=point["close"],
                    volume=point["volume"],
                )
                db.add(ohlcv)

            print(f"  ✅ {market.symbol}: {len(data)} OHLCV-Kerzen generiert (Basis €{base:,.2f})")

        await db.commit()
        print(f"\n✅ Seed abgeschlossen für {len(markets)} Coins")


if __name__ == "__main__":
    asyncio.run(seed_data())
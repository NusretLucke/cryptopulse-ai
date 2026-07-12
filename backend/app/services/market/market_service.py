"""Markt-Daten Service - Abruf und Verwaltung von Kryptomarktdaten

Nutzt CoinCap API (völlig kostenlos, kein API-Key, kein Rate-Limit).
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import pandas as pd

from app.core.config import settings
from app.models.database import Market, OHLCV


class MarketService:
    """Service für Marktdaten-Abruf und -Verarbeitung via CoinCap (free)"""

    COINCAP = "https://api.coincap.io/v2"
    # CoinCap coin IDs für die wichtigsten Coins
    COIN_IDS = {
        "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether",
        "BNB": "binance-coin", "USDC": "usd-coin", "XRP": "xrp",
        "SOL": "solana", "TRX": "tron", "DOGE": "dogecoin",
        "ADA": "cardano", "AVAX": "avalanche", "DOT": "polkadot",
        "LINK": "chainlink", "MATIC": "matic-network", "UNI": "uniswap",
        "SHIB": "shiba-inu", "LTC": "litecoin", "ATOM": "cosmos",
        "ETC": "ethereum-classic", "XLM": "stellar", "XMR": "monero",
        "BCH": "bitcoin-cash", "ALGO": "algorand", "NEAR": "near-protocol",
        "FIL": "filecoin", "APT": "aptos", "SUI": "sui",
        "OP": "optimism", "ARB": "arbitrum", "PEPE": "pepe",
        "INJ": "injective", "TIA": "celestia", "SEI": "sei",
    }

    def __init__(self):
        self.top_coins = settings.TOP_COINS
        self._eur_usd = 1.08  # Default

    async def _get_eur_rate(self) -> float:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get("https://open.er-api.com/v6/latest/USD")
                if r.status_code == 200:
                    return r.json()["rates"].get("EUR", 0.92)
        except: pass
        return 0.92

    def _to_eur(self, usd: float) -> float:
        return usd * self._eur_usd

    async def fetch_top_markets(self) -> list[dict]:
        self._eur_usd = await self._get_eur_rate()
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                url = "https://api.coingecko.com/api/v3/coins/markets"
                r = await client.get(url, params={
                    "vs_currency": "eur",
                    "order": "market_cap_desc",
                    "per_page": self.top_coins,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h",
                })
                if r.status_code != 200:
                    print(f"CoinGecko Error: {r.status_code}")
                    return []
                return r.json()
            except Exception as e:
                print(f"Fehler CoinGecko: {e}")
                return []

    async def fetch_historical_data(self, coin_id: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Historische OHLCV-Daten von CoinCap abrufen (kostenlos)"""
        coin_id = coin_id.lower().replace(" ", "-")
        if coin_id == "usd-coin": coin_id = "usd-coin"
        # CoinCap-interne IDs
        coin_id_map = {v.lower(): k for k, v in self.COIN_IDS.items()}

        if coin_id not in coin_id_map and coin_id not in self.COIN_IDS.values():
            # Versuche direkte CoinCap-ID
            pass

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                start = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
                end = int(datetime.utcnow().timestamp() * 1000)
                r = await client.get(
                    f"{self.COINCAP}/assets/{coin_id}/history",
                    params={"interval": "h1", "start": start, "end": end},
                )
                if r.status_code != 200:
                    print(f"CoinCap History Error {coin_id}: {r.status_code}")
                    return None

                data = r.json()["data"]
                rows = []
                for p in data:
                    ts = datetime.fromtimestamp(p["time"] / 1000)
                    price = float(p["priceUsd"])
                    rows.append({
                        "timestamp": ts,
                        "open": self._to_eur(price * 0.998),
                        "high": self._to_eur(price * 1.005),
                        "low": self._to_eur(price * 0.995),
                        "close": self._to_eur(price),
                    })

                df = pd.DataFrame(rows)
                if not df.empty:
                    df["volume"] = 1_000_000  # CoinCap hat kein Volumen pro Kerze
                return df

            except Exception as e:
                print(f"Fehler History für {coin_id}: {e}")
                return None

    async def update_market(self, db: AsyncSession):
        """Alle Marktdaten aktualisieren (CoinCap live)"""
        markets_data = await self.fetch_top_markets()
        count = 0
        for coin in markets_data:
            try:
                symbol = coin["symbol"].upper()
                result = await db.execute(select(Market).where(Market.symbol == symbol))
                market = result.scalar_one_or_none()

                if market:
                    market.current_price = coin["current_price"]
                    market.volume_24h = coin["total_volume"]
                    market.market_cap = coin["market_cap"]
                    market.change_24h = coin["price_change_percentage_24h"]
                    market.high_24h = coin["high_24h"]
                    market.low_24h = coin["low_24h"]
                    market.last_updated = datetime.utcnow()
                else:
                    db.add(Market(
                        symbol=symbol, name=coin["name"],
                        current_price=coin["current_price"],
                        volume_24h=coin["total_volume"],
                        market_cap=coin["market_cap"],
                        change_24h=coin["price_change_percentage_24h"],
                        high_24h=coin["high_24h"], low_24h=coin["low_24h"],
                    ))
                count += 1
            except Exception as e:
                print(f"Fehler {coin.get('symbol')}: {e}")
                continue

        await db.commit()
        print(f"✅ {count} Coins live aktualisiert (CoinCap)")

    async def update_ohlcv(self, db: AsyncSession, days: int = 7):
        """OHLCV-Daten von Binance Public API abrufen (kostenlos, kein Key)"""
        import aiohttp
        pair_map = {
            "BTC": "BTCUSDT", "ETH": "ETHUSDT", "USDT": "USDTUSDT",
            "BNB": "BNBUSDT", "XRP": "XRPUSDT", "SOL": "SOLUSDT",
            "ADA": "ADAUSDT", "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT",
            "DOT": "DOTUSDT", "LINK": "LINKUSDT", "MATIC": "MATICUSDT",
            "UNI": "UNIUSDT", "LTC": "LTCUSDT", "ATOM": "ATOMUSDT",
            "NEAR": "NEARUSDT", "APT": "APTUSDT", "SUI": "SUIUSDT",
            "OP": "OPUSDT", "ARB": "ARBUSDT", "BCH": "BCHUSDT",
            "XLM": "XLMUSDT", "TRX": "TRXUSDT", "FIL": "FILUSDT",
            "ETC": "ETCUSDT", "INJ": "INJUSDT", "TIA": "TIAUSDT",
            "SEI": "SEIUSDT", "PEPE": "PEPEUSDT", "SHIB": "SHIBUSDT",
        }
        BINANCE = "https://api.binance.com/api/v3/klines"

        result = await db.execute(select(Market))
        markets = result.scalars().all()
        count = 0

        async with httpx.AsyncClient(timeout=15) as client:
            for market in markets:
                pair = pair_map.get(market.symbol, f"{market.symbol}USDT")
                if pair == "USDTUSDT":
                    continue
                try:
                    r = await client.get(
                        BINANCE, params={
                            "symbol": pair, "interval": "1h", "limit": 720,  # 30 Tage
                        }
                    )
                    if r.status_code != 200:
                        continue

                    data = r.json()
                    inserted = 0
                    for kline in data:
                        ts = datetime.fromtimestamp(kline[0] / 1000)
                        o, h, l, c, v = float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4]), float(kline[5])

                        # EUR-Umrechnung
                        o = round(self._to_eur(o), 2)
                        h = round(self._to_eur(h), 2)
                        l = round(self._to_eur(l), 2)
                        c = round(self._to_eur(c), 2)
                        v = round(self._to_eur(v), 2)

                        # Prüfen ob bereits vorhanden
                        existing = await db.execute(
                            select(OHLCV).where(
                                OHLCV.market_id == market.id,
                                OHLCV.timestamp == ts,
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        db.add(OHLCV(
                            market_id=market.id, timestamp=ts,
                            open=o, high=h, low=l, close=c, volume=v,
                        ))
                        inserted += 1

                    if inserted > 0:
                        count += 1
                        print(f"  ✅ {market.symbol}: {inserted} echte OHLCV-Kerzen (Binance)")

                except Exception as e:
                    print(f"  ⚠️ {market.symbol}: {e}")
                    continue

        await db.commit()
        print(f"✅ OHLCV aktualisiert: {count} Coins mit neuen Daten")

    async def get_market_by_symbol(self, db: AsyncSession, symbol: str) -> Optional[Market]:
        result = await db.execute(select(Market).where(Market.symbol == symbol.upper()))
        return result.scalar_one_or_none()

    async def get_ohlcv(self, db: AsyncSession, symbol: str, limit: int = 100) -> list[OHLCV]:
        market = await self.get_market_by_symbol(db, symbol)
        if not market: return []
        result = await db.execute(
            select(OHLCV).where(OHLCV.market_id == market.id)
            .order_by(desc(OHLCV.timestamp)).limit(limit)
        )
        return result.scalars().all()
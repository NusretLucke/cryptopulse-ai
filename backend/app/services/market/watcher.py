"""24/7 Market Watcher — Aktualisiert automatisch alle X Minuten:
1. Live-Kurse von CoinCap (kostenlos)
2. OHLCV-Verlaufsdaten
3. KI-Analyse aller Coins
4. Paper Trade Stop-Loss/Take-Profit Prüfung
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import async_session_factory, init_db
from app.services.market.market_service import MarketService
from app.services.ai.decision_engine import DecisionEngine
from app.services.trading.paper_trading import PaperTradingEngine

logger = logging.getLogger("cryptopulse-watcher")


class MarketWatcher:
    """Autonomer 24/7 Watcher für Marktdaten und KI-Analyse"""

    def __init__(self):
        self.market_service = MarketService()
        self.decision_engine = DecisionEngine()
        self.trading_engine = PaperTradingEngine()
        self._running = False
        self._task = None

    async def run_cycle(self):
        """Ein vollständiger Watcher-Zyklus"""
        try:
            async with async_session_factory() as db:
                now = datetime.utcnow()

                # 1. Live-Kurse abrufen (alle 5 Min)
                logger.info("📊 Hole Live-Kurse von CoinCap...")
                await self.market_service.update_market(db)
                await db.commit()

                # 2. OHLCV-Daten nachladen (alle 30 Min)
                minute = now.minute
                if minute % 30 < 5:  # Alle 30 Minuten
                    logger.info("📈 Aktualisiere OHLCV-Verlaufsdaten...")
                    await self.market_service.update_ohlcv(db, days=7)

                # 3. KI-Analyse für Top-Coins (alle 15 Min)
                if minute % 15 < 5:
                    logger.info("🧠 Führe KI-Analyse für Top-Coins durch...")
                    result = await db.execute(
                        __import__("sqlalchemy").select(
                            __import__("app.models.database", fromlist=["Market"]).Market
                        ).where(
                            __import__("app.models.database", fromlist=["Market"]).Market.current_price.isnot(None)
                        ).limit(20)
                    )
                    markets = result.scalars().all()
                    for market in markets:
                        try:
                            await self.decision_engine.analyze_coin(
                                db, market.symbol, investment_amount=100
                            )
                        except Exception as e:
                            logger.warning(f"  Fehler bei {market.symbol}: {e}")
                    logger.info(f"✅ KI-Analyse für {len(markets)} Coins abgeschlossen")

                # 4. Paper Trades prüfen (Stop-Loss / Take-Profit)
                logger.info("💰 Prüfe offene Paper Trades...")
                await self.trading_engine.update_open_trades(db)

                logger.info(f"✅ Zyklus abgeschlossen um {now.strftime('%H:%M:%S')} UTC")

        except Exception as e:
            logger.error(f"❌ Watcher-Fehler: {e}")

    async def start(self, interval_seconds: int = 300):
        """Watcher im Hintergrund starten (läuft bis Stop)"""
        self._running = True
        logger.info(f"🚀 Market Watcher gestartet (Intervall: {interval_seconds}s)")

        while self._running:
            await self.run_cycle()
            # Warten mit regelmäßigen Checks ob wir stoppen sollen
            for _ in range(interval_seconds):
                if not self._running:
                    break
                await asyncio.sleep(1)

        logger.info("🛑 Market Watcher gestoppt")

    def stop(self):
        """Watcher anhalten"""
        self._running = False


# Globale Instanz
watcher = MarketWatcher()


async def start_watcher():
    """Watcher im Hintergrund starten (wird beim Backend-Start aufgerufen)"""
    await watcher.start(interval_seconds=300)  # Alle 5 Minuten


def stop_watcher():
    """Watcher stoppen"""
    watcher.stop()
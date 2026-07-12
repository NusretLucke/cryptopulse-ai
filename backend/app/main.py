"""Haupt-App für CryptoPulse AI Backend — mit 24/7 KI-Autotrader"""

import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db, close_db
from app.api import market, analysis, trading, auth, dashboard, news, risk, watcher
from app.services.market.watcher import start_trader, stop_trader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown — startet den 24/7 KI-Autotrader"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} wird gestartet...")

    # Datenbank mit Retry (PostgreSQL auf Render braucht manchmal)
    for attempt in range(5):
        try:
            await init_db()
            print(f"✅ Datenbank initialisiert (Versuch {attempt+1})")
            break
        except Exception as e:
            print(f"⏳ DB noch nicht bereit (Versuch {attempt+1}/5): {e}")
            if attempt < 4:
                await asyncio.sleep(3)
            else:
                print(f"⚠️  DB nach 5 Versuchen nicht erreichbar — starte ohne DB")

    # 24/7 KI-Autotrader
    trader_task = asyncio.create_task(start_trader())
    print(f"✅ 24/7 KI-Autotrader gestartet")

    yield

    # Shutdown
    stop_trader()
    trader_task.cancel()
    await close_db()
    print("👋 App heruntergefahren")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="KI-gestützte Krypto-Analyse- und Trading-Plattform — 24/7 KI-Autotrader",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# API Router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(news.router, prefix="/api/news", tags=["News & Sentiment"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Management"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(watcher.router, prefix="/api/watcher", tags=["Watcher"])

# Frontend Static Files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.get("/health")
async def health():
    return {"status": "healthy"}
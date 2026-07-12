"""Haupt-App für CryptoPulse AI Backend — mit 24/7 Watcher"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db, close_db
from app.api import market, analysis, trading, auth, dashboard, news, risk, watcher
from app.services.market.watcher import start_watcher, stop_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown — startet auch den 24/7 Market Watcher"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} wird gestartet...")
    await init_db()
    print(f"✅ Datenbank initialisiert")

    # 24/7 Watcher im Hintergrund starten
    watcher_task = asyncio.create_task(start_watcher())
    print(f"✅ 24/7 Market Watcher gestartet (alle 5 Minuten)")

    yield

    # Shutdown
    stop_watcher()
    watcher_task.cancel()
    await close_db()
    print("👋 App heruntergefahren")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="KI-gestützte Krypto-Analyse- und Trading-Plattform — 24/7 Live-Daten",
    lifespan=lifespan,
)

# CORS — unterstützt lokale und Production-Domains
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(news.router, prefix="/api/news", tags=["News & Sentiment"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Management"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(watcher.router, prefix="/api/watcher", tags=["Watcher"])


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational 🟢 24/7 Watcher aktiv",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
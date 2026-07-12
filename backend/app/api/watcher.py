"""Watcher-API — Status und manuelle Auslösung des 24/7 Markt-Watchers"""

from fastapi import APIRouter, Depends
from app.services.market.watcher import watcher

router = APIRouter()


@router.get("/status")
async def watcher_status():
    """Watcher-Status abrufen"""
    return {
        "running": watcher._running,
        "watcher_24_7": "aktiv 🟢" if watcher._running else "inaktiv 🔴",
        "data_source": "CoinGecko (Kurse) + Binance (OHLCV) — beide kostenlos",
        "update_interval": "Alle 5 Minuten",
        "ohlcv_update": "Alle 30 Minuten",
        "ai_analysis": "Alle 15 Minuten",
    }
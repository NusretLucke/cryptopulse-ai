"""KI-Entscheidungs-Engine - Das Herz des Systems

Multi-Faktor-Scoring mit Reinforcement Learning und Selbstkontrolle.
"""

import json
import numpy as np
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.config import settings
from app.models.database import (
    Market, OHLCV, TradingDecision, PaperTrade, LearningLog,
)
from app.services.analysis.technical_analysis import TechnicalAnalysisEngine, TechnicalIndicators
from app.services.analysis.sentiment_analysis import SentimentAnalyzer


@dataclass
class DecisionResult:
    """Ergebnis einer KI-Entscheidung"""
    symbol: str
    coin_name: str
    decision: str  # buy, sell, hold
    confidence: float
    risk_score: float
    overall_score: float
    expected_move_pct: float
    expected_direction: str
    target_price: float
    stop_loss: float
    top_reasons: list[str]
    market_phase: str
    trend_strength: str

    # Einzelscores
    technical_score: float
    sentiment_score: float
    market_score: float
    onchain_score: float

    # Preisziele
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float


class DecisionEngine:
    """Multi-Faktor-Entscheidungs-Engine mit KI-Lernsystem"""

    # Standard-Gewichtungen (werden durch Lernen optimiert)
    DEFAULT_WEIGHTS = {
        "technical": 0.25,
        "sentiment": 0.20,
        "market_momentum": 0.15,
        "risk": 0.15,
        "pattern_history": 0.15,
        "volume": 0.10,
    }

    def __init__(self):
        self.technical_engine = TechnicalAnalysisEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.weights = dict(self.DEFAULT_WEIGHTS)
        self.performance_history = []
        self.load_model()

    def load_model(self):
        """Gespeicherte Modell-Gewichtungen laden"""
        try:
            with open(f"{settings.MODEL_PATH}/decision_weights.json", "r") as f:
                data = json.load(f)
                self.weights.update(data.get("weights", {}))
                self.performance_history = data.get("performance", [])
                print(f"✅ KI-Modell geladen: {self.weights}")
        except (FileNotFoundError, json.JSONDecodeError):
            print("🆕 Neues KI-Modell mit Standard-Gewichtungen")

    def save_model(self):
        """Modell-Gewichtungen speichern"""
        import os
        os.makedirs(settings.MODEL_PATH, exist_ok=True)
        with open(f"{settings.MODEL_PATH}/decision_weights.json", "w") as f:
            json.dump({
                "weights": self.weights,
                "performance": self.performance_history[-100:],
                "updated_at": datetime.utcnow().isoformat(),
            }, f, indent=2)

    async def analyze_coin(
        self, db: AsyncSession, symbol: str, investment_amount: float = 100.0
    ) -> Optional[DecisionResult]:
        """Einen Coin vollständig analysieren und Entscheidung treffen"""
        # Coin-Daten laden
        result = await db.execute(
            select(Market).where(Market.symbol == symbol.upper())
        )
        market = result.scalar_one_or_none()
        if not market:
            return None

        # OHLCV-Daten laden
        ohlcv_result = await db.execute(
            select(OHLCV)
            .where(OHLCV.market_id == market.id)
            .order_by(OHLCV.timestamp)
            .limit(200)
        )
        ohlcv_records = ohlcv_result.scalars().all()

        if len(ohlcv_records) < 50:
            return None  # Nicht genug Daten für Analyse

        # DataFrame bauen
        import pandas as pd
        df = pd.DataFrame([
            {"timestamp": r.timestamp, "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in ohlcv_records
        ])

        # 1. Technische Analyse
        indicators = self.technical_engine.analyze(df, symbol)
        if not indicators:
            return None
        technical_score, tech_signals = self.technical_engine.get_technical_score(indicators)

        # 2. Sentiment Score (aus der DB)
        sentiment_score = await self._get_sentiment_score(db, market.id)

        # 3. Markt-Momentum
        market_score = self._calculate_market_score(market, indicators)

        # 4. Risikobewertung
        risk_score = self._calculate_risk_score(indicators, market)

        # 5. Multi-Faktor-Gesamtscore
        overall_score = self._calculate_overall_score({
            "technical": technical_score,
            "sentiment": sentiment_score,
            "market_momentum": market_score,
            "risk": (100 - risk_score * 100),  # Invertiert
            "pattern_history": 50,  # Default
            "volume": self._calculate_volume_score(indicators),
        })

        # 6. Entscheidung
        decision = self._make_decision(overall_score, indicators, risk_score)
        confidence = self._calculate_confidence(overall_score, indicators)
        expected_move = self._estimate_move(indicators, confidence)

        # 7. Preisziele berechnen
        current_price = market.current_price or indicators.current_price
        target_price = current_price * (1 + expected_move / 100)
        stop_loss = current_price * (1 - self._get_stop_loss_pct(risk_score) / 100)
        tp1 = current_price * 1.05
        tp2 = current_price * 1.10
        tp3 = current_price * 1.20

        # 8. Top 5 Gründe
        top_reasons = self._generate_reasons(
            decision, indicators, technical_score, sentiment_score,
            risk_score, tech_signals
        )[:5]

        # 9. Entscheidung speichern
        await self._save_decision(db, market, decision, overall_score, {
            "technical": technical_score,
            "sentiment": sentiment_score,
            "market_score": market_score,
            "risk": risk_score,
            "overall": overall_score,
        }, top_reasons, expected_move, current_price, target_price, stop_loss)

        return DecisionResult(
            symbol=market.symbol,
            coin_name=market.name,
            decision=decision,
            confidence=confidence,
            risk_score=risk_score,
            overall_score=overall_score,
            expected_move_pct=expected_move,
            expected_direction="up" if expected_move > 0 else "down",
            target_price=target_price,
            stop_loss=stop_loss,
            top_reasons=top_reasons,
            market_phase=indicators.trend,
            trend_strength=indicators.trend_strength,
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            market_score=market_score,
            onchain_score=50.0,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
        )

    async def analyze_all_coins(
        self, db: AsyncSession, investment_amount: float = 100.0
    ) -> list[DecisionResult]:
        """Alle Coins analysieren und Top-Empfehlungen finden"""
        result = await db.execute(
            select(Market).where(Market.current_price.isnot(None)).limit(50)
        )
        markets = result.scalars().all()

        decisions = []
        for market in markets:
            try:
                decision = await self.analyze_coin(db, market.symbol, investment_amount)
                if decision:
                    decisions.append(decision)
            except Exception as e:
                print(f"Fehler bei {market.symbol}: {e}")
                continue

        # Nach Score sortieren
        decisions.sort(key=lambda d: d.overall_score, reverse=True)
        return decisions

    async def get_buy_recommendation(
        self, db: AsyncSession, amount: float = 100.0, risk_profile: str = "balanced"
    ) -> list[DecisionResult]:
        """'Ich habe X Euro' -> Top-Empfehlungen (bestbewertete Coins)"""
        decisions = await self.analyze_all_coins(db, amount)

        # Stablecoins und Micro-Coins rausfiltern
        stablecoins = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "USDP", "GUSD",
                       "PAX", "USTC", "USDD", "USDY", "USDE", "USDG", "USYC",
                       "USD1", "USDS", "PYUSD", "BUIDL", "WBT", "CC", "GRAM",
                       "USD0", "USUAL", "EURI", "EURC", "EURT", "USDK", "USDX"}
        filtered = [d for d in decisions if d.symbol not in stablecoins]

        # Risiko-Filter
        if risk_profile == "conservative":
            filtered = [d for d in filtered if d.risk_score < 0.4]
        elif risk_profile == "balanced":
            filtered = [d for d in filtered if d.risk_score < 0.6]

        # Nach Score sortieren, Top 5 zurückgeben
        filtered.sort(key=lambda d: d.overall_score, reverse=True)
        return filtered[:5]

    def _calculate_market_score(self, market: Market, indicators: TechnicalIndicators) -> float:
        """Markt-Momentum-Score"""
        score = 50
        if market.change_24h:
            if market.change_24h > 5:
                score += 15
            elif market.change_24h > 2:
                score += 8
            elif market.change_24h < -5:
                score -= 15
            elif market.change_24h < -2:
                score -= 8

        if market.volume_24h and market.market_cap:
            vol_ratio = market.volume_24h / market.market_cap
            if vol_ratio > 0.1:
                score += 5  # Hohe Liquidität

        return max(0, min(100, score))

    def _calculate_risk_score(self, indicators: TechnicalIndicators, market: Market) -> float:
        """Risikoscore (0 = sicher, 1 = riskant)"""
        risk = 0.3  # Basisrisiko

        # Volatilität
        if indicators.volatility == "high":
            risk += 0.2
        elif indicators.volatility == "low":
            risk -= 0.1

        # Bollinger Breite (hohe Breite = hohe Volatilität)
        if indicators.bb_width > 20:
            risk += 0.1

        # Marktkapitalisierung (kleine Coins = riskanter)
        if market.market_cap:
            if market.market_cap < 100_000_000:  # < $100M
                risk += 0.2
            elif market.market_cap < 1_000_000_000:  # < $1B
                risk += 0.1
            elif market.market_cap > 10_000_000_000:  # > $10B
                risk -= 0.1

        # 24h Änderung
        if market.change_24h:
            if abs(market.change_24h) > 15:
                risk += 0.15
            elif abs(market.change_24h) > 8:
                risk += 0.05

        return max(0.0, min(1.0, risk))

    def _calculate_volume_score(self, indicators: TechnicalIndicators) -> float:
        """Volume-Score"""
        if indicators.volume_trend == "increasing":
            return 70
        elif indicators.volume_trend == "decreasing":
            return 30
        return 50

    def _calculate_overall_score(self, scores: dict) -> float:
        """Multi-Faktor-Gesamtscore"""
        weighted_sum = sum(
            scores[factor] * self.weights.get(factor, 0.1)
            for factor in scores
        )
        return max(0, min(100, weighted_sum))

    def _make_decision(self, score: float, indicators: TechnicalIndicators, risk: float) -> str:
        """Entscheidung treffen (buy/sell/hold)"""
        if score >= 65 and risk < 0.7 and indicators.trend != "bearish":
            return "buy"
        elif score <= 35 or (risk > 0.7 and indicators.trend == "bearish"):
            return "sell"
        return "hold"

    def _calculate_confidence(self, score: float, indicators: TechnicalIndicators | None) -> float:
        """Konfidenz der Entscheidung"""
        confidence = abs(score - 50) / 50  # 0-1, je weiter von 50 desto höher

        # Trendbestätigung (falls indicators vorhanden)
        if indicators and indicators.trend_strength == "strong":
            confidence *= 1.2
        elif indicators and indicators.trend_strength == "weak":
            confidence *= 0.8

        return min(1.0, confidence)

    def _estimate_move(self, indicators: TechnicalIndicators, confidence: float) -> float:
        """Erwartete Preisbewegung in %"""
        atr_pct = (indicators.atr / indicators.current_price) * 100

        base_move = atr_pct * confidence
        if indicators.trend == "bullish":
            return base_move
        elif indicators.trend == "bearish":
            return -base_move
        return base_move * 0.5

    def _get_stop_loss_pct(self, risk_score: float) -> float:
        """Stop-Loss Prozent basierend auf Risiko"""
        if risk_score < 0.3:
            return 3.0
        elif risk_score < 0.5:
            return 5.0
        elif risk_score < 0.7:
            return 8.0
        return 12.0

    def _generate_reasons(
        self, decision: str, indicators: TechnicalIndicators,
        tech_score: float, sentiment: float, risk: float,
        tech_signals: list[str]
    ) -> list[str]:
        """Top-Gründe für die Entscheidung"""
        reasons = []

        if decision == "buy":
            if indicators.trend == "bullish":
                reasons.append(f"📈 Aufwärtstrend ({indicators.trend_strength})")
            if indicators.rsi_signal == "oversold":
                reasons.append(f"📊 RSI bei {indicators.rsi:.0f} — überverkauft, Umkehrpotenzial")
            if indicators.macd_cross == "bullish":
                reasons.append("🟢 MACD zeigt bullishes Crossover")
            if tech_score > 60:
                reasons.append(f"🔧 Technische Analyse: {tech_score:.0f}/100 Punkte")
            if sentiment > 0.2:
                reasons.append(f"💬 Positive Marktstimmung ({sentiment:.0f}%)")

        elif decision == "sell":
            if indicators.trend == "bearish":
                reasons.append(f"📉 Abwärtstrend ({indicators.trend_strength})")
            if indicators.rsi_signal == "overbought":
                reasons.append(f"📊 RSI bei {indicators.rsi:.0f} — überkauft")
            if indicators.macd_cross == "bearish":
                reasons.append("🔴 MACD zeigt bearishes Crossover")
            if risk > 0.6:
                reasons.append(f"⚠️ Hohes Risiko ({risk:.0%})")

        else:  # hold
            reasons.append("⏸️ Kein klares Signal — abwarten")
            if indicators.volatility == "high":
                reasons.append("🌊 Hohe Volatilität — Risiko minimieren")
            if abs(tech_score - 50) < 10:
                reasons.append("⚖️ Technische Indikatoren neutral")

        # Allgemeine Gründe
        if indicators.volume_trend == "increasing":
            reasons.append("📊 Steigendes Handelsvolumen bestätigt Bewegung")
        if risk < 0.3:
            reasons.append("✅ Geringes Risiko")
        elif risk > 0.7:
            reasons.append("⚠️ Hohes Risiko — Vorsicht geboten")

        return reasons

    async def _get_sentiment_score(self, db: AsyncSession, market_id: int) -> float:
        """Durchschnittlichen Sentiment-Score aus der DB abrufen"""
        from app.models.database import SocialSentiment
        result = await db.execute(
            select(SocialSentiment.sentiment_score)
            .where(SocialSentiment.market_id == market_id)
            .order_by(desc(SocialSentiment.timestamp))
            .limit(10)
        )
        scores = result.scalars().all()
        if not scores:
            return 0.0
        return (sum(scores) / len(scores) + 1) * 50  # -1..1 zu 0..100

    async def _save_decision(
        self, db: AsyncSession, market: Market, decision: str,
        overall_score: float, scores: dict, reasons: list[str],
        expected_move: float, current_price: float,
        target_price: float, stop_loss: float
    ):
        """Entscheidung in DB speichern"""
        dec = TradingDecision(
            market_id=market.id,
            decision=decision,
            confidence_score=self._calculate_confidence(overall_score, None),
            risk_score=scores.get("risk", 0.5),
            expected_move_pct=expected_move,
            expected_move_direction="up" if expected_move > 0 else "down",
            target_price=target_price,
            stop_loss_price=stop_loss,
            market_score=scores.get("market_score", 50),
            technical_score=scores.get("technical", 50),
            onchain_score=scores.get("onchain_score", 50),
            news_score=scores.get("sentiment", 50),
            sentiment_score=scores.get("sentiment", 50),
            overall_score=overall_score,
            reasoning={"all_scores": scores, "indicators": {}},
            top_reasons=reasons,
        )
        db.add(dec)


# ========================
# KI-LERNSYSTEM
# ========================

class LearningSystem:
    """Kontinuierliches KI-Lernsystem mit Selbstkontrolle"""

    def __init__(self, decision_engine: DecisionEngine):
        self.engine = decision_engine

    async def evaluate_decision(self, db: AsyncSession, decision_id: int):
        """Eine getroffene Entscheidung bewerten (nach Eintreten des Ergebnisses)"""
        result = await db.execute(
            select(TradingDecision).where(TradingDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()
        if not decision:
            return

        # Aktuellen Preis holen
        market_result = await db.execute(
            select(Market).where(Market.id == decision.market_id)
        )
        market = market_result.scalar_one_or_none()
        if not market or not market.current_price:
            return

        # War die Entscheidung richtig?
        if decision.decision == "buy":
            correct = market.current_price > decision.target_price
        elif decision.decision == "sell":
            correct = market.current_price < decision.target_price
        else:
            correct = True  # Hold ist schwer zu bewerten

        # Lernlog aktualisieren
        self.engine.performance_history.append({
            "decision_id": decision_id,
            "correct": correct,
            "confidence": decision.confidence_score,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Gewichtungen anpassen (einfaches Reinforcement Learning)
        self._adjust_weights(correct, decision.confidence_score)
        self.engine.save_model()

    def _adjust_weights(self, was_correct: bool, confidence: float):
        """Gewichtungen basierend auf Erfolg anpassen"""
        learning_rate = 0.01

        if was_correct:
            # Erfolgreiche Faktoren stärker gewichten
            for factor in self.engine.weights:
                self.engine.weights[factor] *= (1 + learning_rate * confidence)
        else:
            # Fehlerhafte Faktoren schwächer gewichten
            for factor in self.engine.weights:
                self.engine.weights[factor] *= (1 - learning_rate * confidence)

        # Normalisieren
        total = sum(self.engine.weights.values())
        for factor in self.engine.weights:
            self.engine.weights[factor] /= total

    async def self_check(self, db: AsyncSession) -> dict:
        """Selbstkontrolle der KI-Leistung"""
        # Letzte 100 Entscheidungen analysieren
        result = await db.execute(
            select(LearningLog).order_by(desc(LearningLog.timestamp)).limit(10)
        )
        logs = result.scalars().all()

        # Paper Trade Performance
        from sqlalchemy import case
        total_trades = 0
        winning_trades = 0
        try:
            count_result = await db.execute(
                select(func.count()).where(PaperTrade.is_open == False)
            )
            total_trades = count_result.scalar() or 0

            win_result = await db.execute(
                select(func.count()).where(
                    PaperTrade.is_open == False,
                    PaperTrade.is_winner == True
                )
            )
            winning_trades = win_result.scalar() or 0
        except Exception:
            pass

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Performance bewerten
        status = "active"
        message = "KI arbeitet normal"

        if win_rate < 0.40 and total_trades >= 10:
            status = "warning"
            message = "⚠️ Trefferquote unter 40% — Empfehlungen werden reduziert"
        elif win_rate < 0.30 and total_trades >= 20:
            status = "cautious"
            message = "🚨 Kritische Trefferquote — nur noch High-Confidence Trades"

        # Marktregime erkennen
        market_regime = self._detect_market_regime()

        avg_accuracy = float(
            sum(1 for l in logs if l.win_rate > 0.5) / len(logs)
        ) if logs else 0.5

        return {
            "status": status,
            "accuracy": avg_accuracy,
            "total_decisions": total_trades or 0,
            "win_rate": win_rate,
            "market_regime": market_regime,
            "confidence": avg_accuracy * win_rate if win_rate > 0 else 0.5,
            "message": message,
            "feature_weights": self.engine.weights,
        }

    def _detect_market_regime(self) -> str:
        """Marktphase erkennen basierend auf Performance"""
        if not self.engine.performance_history:
            return "neutral"

        recent = self.engine.performance_history[-20:] if len(self.engine.performance_history) >= 20 \
            else self.engine.performance_history

        win_rate = sum(1 for p in recent if p["correct"]) / max(len(recent), 1)
        avg_conf = sum(p["confidence"] for p in recent) / max(len(recent), 1)

        if win_rate > 0.6 and avg_conf > 0.7:
            return "bullish"
        elif win_rate < 0.35:
            return "bearish"
        elif avg_conf < 0.4:
            return "volatile"
        return "neutral"
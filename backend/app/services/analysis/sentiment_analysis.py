"""Sentiment-Analyse - KI-gestützte Stimmungsanalyse für News und Social Media"""

from typing import Optional
from textblob import TextBlob
import re


class SentimentAnalyzer:
    """Stimmungsanalyse für Krypto-Nachrichten und Social Media"""

    # Krypto-spezifische positive/negative Begriffe
    POSITIVE_KEYWORDS = [
        "bullish", "moon", "pump", "breakout", "adoption", "partnership",
        "upgrade", "launch", "approval", "positive", "growth", "rally",
        "institutional", "mainnet", "listing", "bullrun",
    ]
    NEGATIVE_KEYWORDS = [
        "bearish", "dump", "crash", "hack", "scam", "regulation", "ban",
        "sell-off", "liquidation", "fud", "delay", "cancel", "exploit",
        "vulnerability", "decline", "rejection", "downgrade",
    ]

    @staticmethod
    def analyze_text(text: str) -> dict:
        """Text auf Stimmung analysieren mit KI-Unterstützung"""
        if not text or len(text.strip()) == 0:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}

        # 1. TextBlob Basis-Analyse
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 bis 1
        subjectivity = blob.sentiment.subjectivity  # 0 bis 1

        # 2. Krypto-spezifische Keyword-Analyse
        text_lower = text.lower()
        pos_count = sum(1 for kw in SentimentAnalyzer.POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in SentimentAnalyzer.NEGATIVE_KEYWORDS if kw in text_lower)

        keyword_score = 0.0
        if pos_count > neg_count:
            keyword_score = min(1.0, (pos_count - neg_count) * 0.15)
        elif neg_count > pos_count:
            keyword_score = max(-1.0, (neg_count - pos_count) * -0.15)

        # 3. Gewichteter Gesamtscore
        # TextBlob (60%) + Keyword (40%)
        final_score = (polarity * 0.6) + (keyword_score * 0.4)
        final_score = max(-1.0, min(1.0, final_score))

        # Label bestimmen
        if final_score > 0.2:
            label = "positiv"
        elif final_score < -0.2:
            label = "negativ"
        else:
            label = "neutral"

        # Confidence
        confidence = min(1.0, abs(final_score) + (subjectivity * 0.3))

        return {
            "score": round(final_score, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "keyword_score": round(keyword_score, 4),
        }

    @staticmethod
    def extract_coins(text: str, top_coins: list[str]) -> list[str]:
        """Erwähnte Kryptowährungen aus Text extrahieren"""
        text_lower = text.lower()
        found = []
        for coin in top_coins:
            coin_lower = coin.lower()
            if coin_lower in text_lower:
                found.append(coin.upper())
        return found

    @staticmethod
    def calculate_impact_score(sentiment: dict, source_authority: float = 0.5) -> float:
        """Impact-Score berechnen (wie wichtig ist diese Nachricht)"""
        impact = abs(sentiment["score"]) * sentiment["confidence"] * source_authority
        return round(min(1.0, impact), 4)

    @staticmethod
    def classify_categories(text: str) -> list[str]:
        """Themen-Kategorien identifizieren"""
        categories = []
        text_lower = text.lower()

        category_keywords = {
            "regulation": ["regulation", "sec", "regulatory", "ban", "legal", "compliance", "gesetz"],
            "technology": ["upgrade", "mainnet", "protocol", "layer2", "scaling", "fork", "technology"],
            "partnership": ["partnership", "collaboration", "alliance", "strategic", "integrate"],
            "market": ["price", "market", "trading", "volume", "rally", "crash", "bull", "bear"],
            "adoption": ["adoption", "institutional", "payment", "merchant", "mainstream"],
            "security": ["hack", "exploit", "breach", "attack", "vulnerability", "security"],
            "defi": ["defi", "lending", "staking", "yield", "liquidity", "protocol"],
            "nft": ["nft", "collectible", "tokenization", "digital art"],
        }

        for cat, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                categories.append(cat)

        return categories if categories else ["general"]

    @staticmethod
    def summarize_impact(sentiment_score: float, impact_score: float) -> str:
        """Menschlich lesbare Auswirkung generieren"""
        if abs(sentiment_score) < 0.15:
            return "Keine signifikante Auswirkung erwartet"

        direction = "positive" if sentiment_score > 0 else "negative"
        strength = "starke" if impact_score > 0.7 else "moderate" if impact_score > 0.4 else "geringe"

        return f"{strength} {direction}e Auswirkung auf den Kurs erwartet"


class FakeNewsDetector:
    """Erkennung von manipulierten Nachrichten und Bot-Aktivität"""

    @staticmethod
    def analyze_social_pattern(mentions: list[dict], time_window_hours: int = 1) -> dict:
        """Social-Media-Muster auf Manipulation prüfen"""
        if not mentions or len(mentions) < 5:
            return {"is_suspicious": False, "bot_score": 0.0, "reason": "Zu wenig Daten"}

        # Zeitliche Verteilung prüfen
        timestamps = [m.get("timestamp") for m in mentions]
        if len(timestamps) < 2:
            return {"is_suspicious": False, "bot_score": 0.0}

        # Auf Spikes prüfen (plötzlicher Anstieg)
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i - 1]
            time_diffs.append(diff.total_seconds() if hasattr(diff, 'total_seconds') else 0)

        if not time_diffs:
            return {"is_suspicious": False, "bot_score": 0.0}

        avg_gap = sum(time_diffs) / len(time_diffs)
        uniform_activity = all(abs(d - avg_gap) < 1.0 for d in time_diffs[:10])

        bot_score = 0.3 if uniform_activity else 0.0

        return {
            "is_suspicious": bot_score > 0.5,
            "bot_score": bot_score,
            "reason": "Verdächtig gleichmäßige Aktivität" if uniform_activity else "Normales Muster",
        }
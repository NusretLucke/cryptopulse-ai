"""Technische Analyse Engine - Berechnung aller Indikatoren"""

import pandas as pd
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class TechnicalIndicators:
    """Alle berechneten Indikatoren für einen Coin"""
    symbol: str
    current_price: float
    rsi: float
    rsi_signal: str  # overbought, oversold, neutral
    macd: float
    macd_signal: float
    macd_histogram: float
    macd_cross: str  # bullish, bearish, none
    ema_12: float
    ema_26: float
    ema_signal: str  # bullish (12>26), bearish (12<26)
    sma_20: float
    sma_50: float
    sma_200: Optional[float]
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: str  # above_upper, inside, below_lower
    bb_width: float
    atr: float
    supports: list[float]
    resistances: list[float]
    trend: str  # bullish, bearish, sideways
    trend_strength: str  # weak, moderate, strong
    volume_trend: str  # increasing, decreasing, stable
    volatility: str  # low, medium, high


class TechnicalAnalysisEngine:
    """Vollständige technische Analyse"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """RSI (Relative Strength Index) berechnen"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0

    @staticmethod
    def calculate_macd(prices: pd.Series) -> tuple[float, float, float, str]:
        """MACD berechnen"""
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        # Kreuzung erkennen
        if len(macd) < 2:
            return float(macd.iloc[-1]), float(signal.iloc[-1]), float(histogram.iloc[-1]), "none"

        cross = "bullish" if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2] else \
                "bearish" if macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2] else "none"

        return float(macd.iloc[-1]), float(signal.iloc[-1]), float(histogram.iloc[-1]), cross

    @staticmethod
    def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple[float, float, float, str, float]:
        """Bollinger Bänder berechnen"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        current_price = float(prices.iloc[-1])
        bb_upper = float(upper.iloc[-1])
        bb_middle = float(sma.iloc[-1])
        bb_lower = float(lower.iloc[-1])
        bb_width = ((bb_upper - bb_lower) / bb_middle) * 100

        # Position bestimmen
        if current_price >= bb_upper:
            position = "above_upper"
        elif current_price <= bb_lower:
            position = "below_lower"
        else:
            position = "inside"

        return bb_upper, bb_middle, bb_lower, position, bb_width

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
        """ATR (Average True Range) berechnen"""
        high, low, close = df["high"], df["low"], df["close"]
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1]) if not atr.empty else 0.0

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 5) -> tuple[list[float], list[float]]:
        """Unterstützungen und Widerstände finden"""
        highs = df["high"].values
        lows = df["low"].values
        supports = []
        resistances = []

        for i in range(window, len(df) - window):
            # Lokale Tiefs (Supports)
            if all(lows[i] <= lows[i - j] for j in range(1, window + 1)) and \
               all(lows[i] <= lows[i + j] for j in range(1, window + 1)):
                supports.append(float(lows[i]))

            # Lokale Hochs (Resistances)
            if all(highs[i] >= highs[i - j] for j in range(1, window + 1)) and \
               all(highs[i] >= highs[i + j] for j in range(1, window + 1)):
                resistances.append(float(highs[i]))

        # Nächste Unterstützung/Widerstand zum aktuellen Preis
        current_price = float(df["close"].iloc[-1])
        supports = sorted([s for s in supports if s < current_price], reverse=True)[:3]
        resistances = sorted([r for r in resistances if r > current_price])[:3]

        return supports, resistances

    @staticmethod
    def determine_trend(ema_12: float, ema_26: float, sma_50: float, current_price: float) -> tuple[str, str]:
        """Trendrichtung und -stärke bestimmen"""
        # Richtung
        if ema_12 > ema_26 and current_price > sma_50:
            trend = "bullish"
        elif ema_12 < ema_26 and current_price < sma_50:
            trend = "bearish"
        else:
            trend = "sideways"

        # Stärke
        ema_diff_pct = abs(ema_12 - ema_26) / ema_26 * 100
        if ema_diff_pct > 3:
            strength = "strong"
        elif ema_diff_pct > 1:
            strength = "moderate"
        else:
            strength = "weak"

        return trend, strength

    @staticmethod
    def analyze_volume(volume: pd.Series, volume_sma: pd.Series) -> str:
        """Volumen-Trend analysieren"""
        if len(volume) < 10:
            return "stable"

        recent_vol = volume.iloc[-5:].mean()
        older_vol = volume.iloc[-10:-5].mean()

        if recent_vol > older_vol * 1.2:
            return "increasing"
        elif recent_vol < older_vol * 0.8:
            return "decreasing"
        return "stable"

    @staticmethod
    def analyze_volatility(atr: float, current_price: float) -> str:
        """Volatilität einschätzen"""
        atr_pct = (atr / current_price) * 100
        if atr_pct > 5:
            return "high"
        elif atr_pct > 2:
            return "medium"
        return "low"

    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TechnicalIndicators]:
        """Vollständige technische Analyse durchführen"""
        if df.empty or len(df) < 50:
            return None

        prices = df["close"]
        current_price = float(prices.iloc[-1])

        # Indikatoren berechnen
        rsi = self.calculate_rsi(prices)
        rsi_signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"

        macd_val, macd_sig, macd_hist, macd_cross = self.calculate_macd(prices)
        ema_12 = float(prices.ewm(span=12, adjust=False).mean().iloc[-1])
        ema_26 = float(prices.ewm(span=26, adjust=False).mean().iloc[-1])
        ema_signal = "bullish" if ema_12 > ema_26 else "bearish"

        sma_20 = float(prices.rolling(20).mean().iloc[-1])
        sma_50 = float(prices.rolling(50).mean().iloc[-1])
        sma_200 = float(prices.rolling(200).mean().iloc[-1]) if len(prices) >= 200 else None

        bb_upper, bb_middle, bb_lower, bb_pos, bb_width = self.calculate_bollinger(prices)
        atr = self.calculate_atr(df)

        supports, resistances = self.find_support_resistance(df)
        trend, trend_strength = self.determine_trend(ema_12, ema_26, sma_50, current_price)

        volume_sma = df["volume"].rolling(20).mean()
        volume_trend = self.analyze_volume(df["volume"], volume_sma)
        volatility = self.analyze_volatility(atr, current_price)

        return TechnicalIndicators(
            symbol=symbol,
            current_price=current_price,
            rsi=rsi, rsi_signal=rsi_signal,
            macd=macd_val, macd_signal=macd_sig,
            macd_histogram=macd_hist, macd_cross=macd_cross,
            ema_12=ema_12, ema_26=ema_26, ema_signal=ema_signal,
            sma_20=sma_20, sma_50=sma_50, sma_200=sma_200,
            bb_upper=bb_upper, bb_middle=bb_middle, bb_lower=bb_lower,
            bb_position=bb_pos, bb_width=bb_width,
            atr=atr,
            supports=supports, resistances=resistances,
            trend=trend, trend_strength=trend_strength,
            volume_trend=volume_trend, volatility=volatility,
        )

    def get_technical_score(self, indicators: TechnicalIndicators) -> tuple[float, dict]:
        """Technischen Score berechnen (0-100)"""
        score = 50  # Neutral
        signals = []

        # RSI (30%)
        if indicators.rsi_signal == "oversold":
            score += 15
            signals.append("RSI zeigt überverkauft → Kaufsignal")
        elif indicators.rsi_signal == "overbought":
            score -= 15
            signals.append("RSI zeigt überkauft → Verkaufssignal")

        # MACD (25%)
        if indicators.macd_cross == "bullish":
            score += 12
            signals.append("MACD bullish crossover → Kaufsignal")
        elif indicators.macd_cross == "bearish":
            score -= 12
            signals.append("MACD bearish crossover → Verkaufssignal")

        # EMA-Trend (20%)
        if indicators.ema_signal == "bullish":
            score += 10
        else:
            score -= 10

        # Bollinger Bänder (15%)
        if indicators.bb_position == "below_lower":
            score += 8
            signals.append("Preis unter unterem Bollinger Band → potenzielle Umkehr")
        elif indicators.bb_position == "above_upper":
            score -= 8
            signals.append("Preis über oberem Bollinger Band → überdehnt")

        # Trend (10%)
        if indicators.trend == "bullish":
            score += 5
        elif indicators.trend == "bearish":
            score -= 5

        # Volumen Bestätigung (optional)
        if indicators.volume_trend == "increasing" and indicators.trend == "bullish":
            score += 5
            signals.append("Steigendes Volumen bestätigt Aufwärtstrend")

        score = max(0, min(100, score))
        return score, signals
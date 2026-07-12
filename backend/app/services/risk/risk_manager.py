"""Risk Management - Sicherheits- und Risikokontrollen"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskAssessment:
    """Risikobewertung für eine geplante Investition"""
    is_safe: bool
    risk_level: str  # low, medium, high, critical
    max_position_size: float  # In EUR
    max_position_pct: float  # % des Portfolios
    stop_loss_recommended: float  # In %
    take_profit_recommended: float  # In %
    reasons: list[str]
    warnings: list[str]


class RiskManager:
    """Umfassendes Risikomanagement-System"""

    def __init__(self, max_position_pct: float = 10.0, max_daily_loss_pct: float = 5.0):
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct

    def assess_trade(
        self, symbol: str, amount: float, portfolio_value: float,
        coin_volatility: float, market_cap: float,
        daily_pnl: float, existing_positions: list[dict],
    ) -> RiskAssessment:
        """Vollständige Risikobewertung für einen Trade"""
        reasons = []
        warnings = []
        is_safe = True

        # 1. Positionsgrößen-Check
        position_pct = (amount / portfolio_value) * 100 if portfolio_value > 0 else 100
        if position_pct > self.max_position_pct:
            max_amount = portfolio_value * (self.max_position_pct / 100)
            warnings.append(
                f"⚠️ Positionsgröße ({position_pct:.1f}%) überschreitet Limit ({self.max_position_pct}%). "
                f"Maximal erlaubt: {max_amount:.2f}€"
            )
            is_safe = False

        # 2. Verlustlimits
        if abs(daily_pnl) > portfolio_value * (self.max_daily_loss_pct / 100):
            warnings.append(
                f"🚨 Tagesverlust-Limit ({self.max_daily_loss_pct}%) erreicht. "
                "Keine weiteren Trades heute empfohlen."
            )
            is_safe = False

        # 3. Diversifikation
        if existing_positions:
            same_coin_positions = [p for p in existing_positions if p.get("symbol") == symbol]
            if same_coin_positions:
                warnings.append(f"⚠️ Bereits Position in {symbol} vorhanden. Prüfe Gesamt-Exposure.")
                total_existing = sum(p.get("value", 0) for p in same_coin_positions)
                if total_existing + amount > portfolio_value * (self.max_position_pct / 100):
                    warnings.append(f"🚨 Maximales Exposure für {symbol} erreicht")
                    is_safe = False

        # 4. Liquiditätsprüfung (Marktkapitalisierung)
        if market_cap < 10_000_000:  # < $10M
            warnings.append("⚠️ Sehr geringe Marktkapitalisierung — hohes Risiko")
        elif market_cap < 100_000_000:  # < $100M
            warnings.append("ℹ️ Geringe Marktkapitalisierung — erhöhtes Risiko")

        # 5. Volatilitätsprüfung
        if coin_volatility > 10:
            warnings.append(f"🌊 Hohe Volatilität ({coin_volatility:.1f}%)")
        elif coin_volatility > 5:
            pass  # Moderate Volatilität ist normal

        # 6. Risikostufe bestimmen
        if not is_safe:
            risk_level = "critical"
        elif len(warnings) >= 3:
            risk_level = "high"
        elif len(warnings) >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 7. Stop-Loss / Take-Profit Empfehlungen
        if risk_level == "low":
            sl = 3.0
            tp = 10.0
        elif risk_level == "medium":
            sl = 5.0
            tp = 15.0
        elif risk_level == "high":
            sl = 8.0
            tp = 20.0
        else:
            sl = 12.0
            tp = 25.0

        reasons.append(f"📊 Positionsgröße: {position_pct:.1f}% des Portfolios")
        reasons.append(f"🛑 Empfohlener Stop-Loss: {sl:.0f}%")
        reasons.append(f"🎯 Empfohlenes Take-Profit: {tp:.0f}%")

        return RiskAssessment(
            is_safe=is_safe,
            risk_level=risk_level,
            max_position_size=portfolio_value * (self.max_position_pct / 100),
            max_position_pct=self.max_position_pct,
            stop_loss_recommended=sl,
            take_profit_recommended=tp,
            reasons=reasons,
            warnings=warnings,
        )

    @staticmethod
    def check_scam_risk(symbol: str, market_cap: float, volume_24h: float,
                        price_change_24h: float, holder_count: int) -> dict:
        """Scam-Risiko prüfen"""
        risk_score = 0.0
        flags = []

        # Extrem niedrige Marktkapitalisierung
        if market_cap < 1_000_000:
            risk_score += 0.3
            flags.append("Micro-Cap Coin")

        # Ungewöhnlich hohe Preisänderung
        if abs(price_change_24h) > 100:
            risk_score += 0.2
            flags.append("Extreme Preisbewegung (>100% in 24h)")

        # Geringe Liquidität
        if market_cap > 0 and volume_24h / market_cap < 0.01:
            risk_score += 0.2
            flags.append("Sehr geringe Liquidität")

        # Wenige Holder
        if holder_count and holder_count < 100:
            risk_score += 0.3
            flags.append("Wenige Inhaber (<100)")

        return {
            "risk_score": min(1.0, risk_score),
            "is_suspicious": risk_score > 0.5,
            "flags": flags,
            "recommendation": "Vorsicht geboten" if risk_score > 0.3 else "Scheint sicher",
        }

    @staticmethod
    def emergency_kill_switch(trades_last_hour: int, max_trades_per_hour: int = 5) -> bool:
        """Not-Aus: Zu viele Trades in kurzer Zeit"""
        return trades_last_hour >= max_trades_per_hour
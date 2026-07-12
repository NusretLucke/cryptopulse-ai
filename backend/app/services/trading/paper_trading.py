"""Paper Trading Engine - Simulierte Trades mit vollständiger Erfolgskontrolle"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.database import PaperTrade, Market, TradingDecision
from app.schemas.schemas import PaperTradeResponse, PaperTradeResult


class PaperTradingEngine:
    """Verwaltet alle simulierten Trades"""

    async def create_trade(
        self, db: AsyncSession, symbol: str, entry_price: float,
        amount: float, strategy: str = "ai_decision",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        decision_id: Optional[int] = None,
    ) -> PaperTrade:
        """Neuen Paper Trade eröffnen"""
        market_result = await db.execute(
            select(Market).where(Market.symbol == symbol.upper())
        )
        market = market_result.scalar_one_or_none()
        if not market:
            raise ValueError(f"Coin {symbol} nicht gefunden")

        quantity = amount / entry_price

        trade = PaperTrade(
            market_id=market.id,
            symbol=symbol.upper(),
            entry_price=entry_price,
            amount=amount,
            quantity=quantity,
            entry_time=datetime.utcnow(),
            is_open=True,
            strategy_name=strategy,
            decision_id=decision_id,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        db.add(trade)
        await db.flush()
        return trade

    async def close_trade(self, db: AsyncSession, trade_id: int, exit_price: float) -> Optional[PaperTrade]:
        """Trade schließen und Ergebnis berechnen"""
        result = await db.execute(
            select(PaperTrade).where(PaperTrade.id == trade_id, PaperTrade.is_open == True)
        )
        trade = result.scalar_one_or_none()
        if not trade:
            return None

        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.is_open = False

        # Gewinn/Verlust berechnen
        trade.profit_loss = (exit_price - trade.entry_price) * trade.quantity
        trade.profit_loss_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        trade.is_winner = trade.profit_loss > 0

        await db.flush()
        return trade

    async def update_open_trades(self, db: AsyncSession):
        """Offene Trades auf Stop-Loss/Take-Profit prüfen"""
        result = await db.execute(
            select(PaperTrade).where(PaperTrade.is_open == True)
        )
        open_trades = result.scalars().all()

        for trade in open_trades:
            market_result = await db.execute(
                select(Market).where(Market.symbol == trade.symbol)
            )
            market = market_result.scalar_one_or_none()
            if not market or not market.current_price:
                continue

            current_price = market.current_price

            # Stop-Loss Check
            if trade.stop_loss and current_price <= trade.stop_loss:
                if not trade.stop_loss_hit:
                    trade.stop_loss_hit = True
                    await self.close_trade(db, trade.id, trade.stop_loss)

            # Take-Profit Check
            elif trade.take_profit and current_price >= trade.take_profit:
                if not trade.take_profit_hit:
                    trade.take_profit_hit = True
                    await self.close_trade(db, trade.id, trade.take_profit)

    async def get_portfolio(self, db: AsyncSession) -> dict:
        """Aktuelles Portfolio mit offenen Positionen"""
        # Offene Positionen
        result = await db.execute(
            select(PaperTrade).where(PaperTrade.is_open == True)
        )
        open_trades = result.scalars().all()

        # Portfolio-Wert berechnen
        total_invested = 0.0
        current_value = 0.0
        cash = 10000.0  # Startkapital für Paper Trading

        positions = []
        for trade in open_trades:
            market_result = await db.execute(
                select(Market).where(Market.symbol == trade.symbol)
            )
            market = market_result.scalar_one_or_none()
            current_price = market.current_price if market else trade.entry_price

            position_value = trade.quantity * current_price
            invested = trade.amount

            total_invested += invested
            current_value += position_value
            cash -= invested

            positions.append({
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "entry_price": trade.entry_price,
                "current_price": current_price,
                "value": position_value,
                "pnl": position_value - invested,
                "pnl_pct": ((current_price - trade.entry_price) / trade.entry_price) * 100,
            })

        # Geschlossene Trades
        result = await db.execute(
            select(func.count(), func.sum(PaperTrade.profit_loss))
            .where(PaperTrade.is_open == False)
        )
        closed_count, total_pnl = result.one()

        return {
            "cash": cash,
            "invested": total_invested,
            "current_value": current_value,
            "total_value": cash + current_value,
            "total_pnl": total_pnl or 0,
            "open_positions": positions,
            "closed_trades": closed_count or 0,
        }

    async def get_performance(self, db: AsyncSession) -> PaperTradeResult:
        """Gesamtperformance aller Trades"""
        # Alle geschlossenen Trades
        result = await db.execute(
            select(PaperTrade)
            .where(PaperTrade.is_open == False)
            .order_by(desc(PaperTrade.exit_time))
        )
        closed_trades = result.scalars().all()

        total = len(closed_trades)
        if total == 0:
            return PaperTradeResult(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, total_profit_loss=0.0,
                avg_profit_per_trade=0.0, open_positions=0,
            )

        winning = sum(1 for t in closed_trades if t.is_winner)
        losing = total - winning
        total_pnl = sum(t.profit_loss or 0 for t in closed_trades)

        # Beste/schlechteste Trades
        sorted_by_pnl = sorted(closed_trades, key=lambda t: t.profit_loss or 0)
        worst = sorted_by_pnl[0] if sorted_by_pnl else None
        best = sorted_by_pnl[-1] if sorted_by_pnl else None

        # Offene Positionen zählen
        open_result = await db.execute(
            select(func.count()).where(PaperTrade.is_open == True)
        )
        open_count = open_result.scalar() or 0

        return PaperTradeResult(
            total_trades=total,
            winning_trades=winning,
            losing_trades=losing,
            win_rate=winning / total * 100 if total > 0 else 0,
            total_profit_loss=total_pnl,
            avg_profit_per_trade=total_pnl / total if total > 0 else 0,
            open_positions=open_count,
            best_trade=self._to_response(best),
            worst_trade=self._to_response(worst),
        )

    def _to_response(self, trade: Optional[PaperTrade]) -> Optional[PaperTradeResponse]:
        if not trade:
            return None
        return PaperTradeResponse(
            id=trade.id, symbol=trade.symbol,
            entry_price=trade.entry_price, amount=trade.amount,
            quantity=trade.quantity, entry_time=trade.entry_time,
            exit_price=trade.exit_price, profit_loss=trade.profit_loss,
            profit_loss_pct=trade.profit_loss_pct,
            is_open=trade.is_open, is_winner=trade.is_winner,
            strategy_name=trade.strategy_name,
        )
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


logger = logging.getLogger(__name__)


@dataclass
class Position:
    side: str
    symbol: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    fees_paid: float = 0.0


@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    gross_pnl: float
    fees: float
    net_pnl: float
    exit_reason: str


class PaperExecutionEngine:
    """
    Simulates trade execution.

    IMPORTANT:
    This class never sends orders to Binance
    or any other exchange.
    """

    def __init__(
        self,
        starting_balance: float = 1000.0,
        fee_rate: float = 0.001,
        symbol: str = "ETHUSDT",
    ):
        if starting_balance <= 0:
            raise ValueError(
                "Starting balance must be greater than 0."
            )

        if fee_rate < 0:
            raise ValueError(
                "Fee rate cannot be negative."
            )

        self.symbol = symbol.upper()

        self.starting_balance = starting_balance

        self.cash = starting_balance

        self.fee_rate = fee_rate

        self.position: Optional[Position] = None

        self.trade_history: List[Trade] = []

        self.realized_pnl = 0.0

        self.last_price: Optional[float] = None

    # --------------------------------------------------
    # BUY
    # --------------------------------------------------

    def open_long(
        self,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> dict:

        if self.position is not None:
            return {
                "success": False,
                "reason": "A position is already open.",
            }

        if quantity <= 0:
            return {
                "success": False,
                "reason": "Quantity must be greater than 0.",
            }

        if entry_price <= 0:
            return {
                "success": False,
                "reason": "Entry price must be greater than 0.",
            }

        if stop_loss >= entry_price:
            return {
                "success": False,
                "reason": "Stop loss must be below entry price.",
            }

        if take_profit <= entry_price:
            return {
                "success": False,
                "reason": "Take profit must be above entry price.",
            }

        position_value = (
            quantity * entry_price
        )

        entry_fee = (
            position_value * self.fee_rate
        )

        total_cost = (
            position_value + entry_fee
        )

        if total_cost > self.cash:
            return {
                "success": False,
                "reason": "Insufficient cash.",
            }

        self.cash -= total_cost

        now = datetime.now(timezone.utc)

        self.position = Position(
            side="LONG",
            symbol=self.symbol,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=now,
            fees_paid=entry_fee,
        )

        self.last_price = entry_price

        logger.info(
            "PAPER BUY | %s | quantity=%.8f | price=%.2f",
            self.symbol,
            quantity,
            entry_price,
        )

        return {
            "success": True,
            "action": "BUY",
            "symbol": self.symbol,
            "quantity": quantity,
            "price": entry_price,
            "fee": entry_fee,
        }

    # --------------------------------------------------
    # MARKET PRICE UPDATE
    # --------------------------------------------------

    def update_price(
        self,
        price: float,
    ) -> dict:

        if price <= 0:
            raise ValueError(
                "Price must be greater than 0."
            )

        self.last_price = price

        if self.position is None:

            return {
                "position_open": False,
                "closed": False,
                "reason": "No open position.",
            }

        position = self.position

        # Take profit

        if price >= position.take_profit:

            return self.close_position(
                price=position.take_profit,
                reason="TAKE_PROFIT",
            )

        # Stop loss

        if price <= position.stop_loss:

            return self.close_position(
                price=position.stop_loss,
                reason="STOP_LOSS",
            )

        return {
            "position_open": True,
            "closed": False,
            "unrealized_pnl": self.unrealized_pnl(),
        }

    # --------------------------------------------------
    # CLOSE POSITION
    # --------------------------------------------------

    def close_position(
        self,
        price: float,
        reason: str = "MANUAL",
    ) -> dict:

        if self.position is None:

            return {
                "success": False,
                "reason": "No open position.",
            }

        position = self.position

        exit_value = (
            position.quantity * price
        )

        exit_fee = (
            exit_value * self.fee_rate
        )

        gross_pnl = (
            price - position.entry_price
        ) * position.quantity

        total_fees = (
            position.fees_paid
            + exit_fee
        )

        net_pnl = (
            gross_pnl - total_fees
        )

        # Return sale proceeds to cash.

        self.cash += (
            exit_value - exit_fee
        )

        self.realized_pnl += net_pnl

        now = datetime.now(timezone.utc)

        trade = Trade(
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=price,
            entry_time=position.entry_time,
            exit_time=now,
            gross_pnl=gross_pnl,
            fees=total_fees,
            net_pnl=net_pnl,
            exit_reason=reason,
        )

        self.trade_history.append(trade)

        self.position = None

        self.last_price = price

        logger.info(
            "PAPER SELL | %s | price=%.2f | "
            "net_pnl=%.4f | reason=%s",
            self.symbol,
            price,
            net_pnl,
            reason,
        )

        return {
            "success": True,
            "closed": True,
            "exit_price": price,
            "gross_pnl": gross_pnl,
            "fees": total_fees,
            "net_pnl": net_pnl,
            "reason": reason,
        }

    # --------------------------------------------------
    # UNREALIZED P&L
    # --------------------------------------------------

    def unrealized_pnl(self) -> float:

        if self.position is None:
            return 0.0

        if self.last_price is None:
            return 0.0

        position = self.position

        return (
            self.last_price
            - position.entry_price
        ) * position.quantity

    # --------------------------------------------------
    # EQUITY
    # --------------------------------------------------

    def equity(self) -> float:

        if self.position is None:
            return self.cash

        position_value = (
            self.position.quantity
            * self.last_price
        )

        return (
            self.cash
            + position_value
        )

    # --------------------------------------------------
    # TOTAL RETURN
    # --------------------------------------------------

    def total_return(self) -> float:

        return (
            self.equity()
            - self.starting_balance
        )

    # --------------------------------------------------
    # POSITION STATUS
    # --------------------------------------------------

    def get_position(self) -> Optional[dict]:

        if self.position is None:
            return None

        position = self.position

        return {
            "symbol": position.symbol,
            "side": position.side,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "stop_loss": position.stop_loss,
            "take_profit": position.take_profit,
            "unrealized_pnl": self.unrealized_pnl(),
        }

    # --------------------------------------------------
    # ACCOUNT STATUS
    # --------------------------------------------------

    def account_status(self) -> dict:

        return {
            "starting_balance": self.starting_balance,
            "cash": self.cash,
            "equity": self.equity(),
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl(),
            "total_return": self.total_return(),
            "open_position": self.get_position(),
            "total_trades": len(
                self.trade_history
            ),
        }
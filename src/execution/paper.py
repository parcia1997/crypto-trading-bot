import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


logger = logging.getLogger(__name__)


# ============================================================
# DATA MODELS
# ============================================================

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


# ============================================================
# PAPER EXECUTION ENGINE
# ============================================================

class PaperExecutionEngine:
    """
    Simulates paper-trading execution.

    IMPORTANT:
    This class never sends real orders to Binance.

    Supports:
        - LONG positions
        - Entry fee
        - Exit fee
        - Take profit
        - Stop loss
        - Live price updates
        - OHLC candle updates for backtesting
        - Trade history
        - Realized P&L
        - Unrealized P&L
        - Account equity
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

        self.starting_balance = (
            starting_balance
        )

        self.cash = (
            starting_balance
        )

        self.fee_rate = (
            fee_rate
        )

        self.position: Optional[
            Position
        ] = None

        self.trade_history: List[
            Trade
        ] = []

        self.realized_pnl = 0.0

        self.last_price: Optional[
            float
        ] = None

    # ========================================================
    # OPEN LONG POSITION
    # ========================================================

    def open_long(
        self,
        quantity: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """
        Open a simulated LONG position.
        """

        if self.position is not None:

            return {
                "success": False,
                "reason":
                    "A position is already open.",
            }

        if quantity <= 0:

            return {
                "success": False,
                "reason":
                    "Quantity must be greater than 0.",
            }

        if entry_price <= 0:

            return {
                "success": False,
                "reason":
                    "Entry price must be greater than 0.",
            }

        if stop_loss >= entry_price:

            return {
                "success": False,
                "reason":
                    "Stop loss must be below entry price.",
            }

        if take_profit <= entry_price:

            return {
                "success": False,
                "reason":
                    "Take profit must be above entry price.",
            }

        # ----------------------------------------------------
        # POSITION VALUE
        # ----------------------------------------------------

        position_value = (
            quantity
            * entry_price
        )

        # ----------------------------------------------------
        # ENTRY FEE
        # ----------------------------------------------------

        entry_fee = (
            position_value
            * self.fee_rate
        )

        # ----------------------------------------------------
        # TOTAL COST
        # ----------------------------------------------------

        total_cost = (
            position_value
            + entry_fee
        )

        if total_cost > self.cash:

            return {
                "success": False,
                "reason":
                    "Insufficient cash.",
            }

        # ----------------------------------------------------
        # DEDUCT CASH
        # ----------------------------------------------------

        self.cash -= total_cost

        now = datetime.now(
            timezone.utc
        )

        # ----------------------------------------------------
        # CREATE POSITION
        # ----------------------------------------------------

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

        self.last_price = (
            entry_price
        )

        logger.info(
            "PAPER BUY | %s | "
            "quantity=%.8f | "
            "price=%.2f | "
            "fee=%.4f | "
            "SL=%.2f | "
            "TP=%.2f",
            self.symbol,
            quantity,
            entry_price,
            entry_fee,
            stop_loss,
            take_profit,
        )

        return {
            "success": True,
            "action": "BUY",
            "symbol": self.symbol,
            "quantity": quantity,
            "price": entry_price,
            "fee": entry_fee,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }

    # ========================================================
    # LIVE MARKET PRICE UPDATE
    # ========================================================

    def update_price(
        self,
        price: float,
    ) -> dict:
        """
        Update the current market price.

        Intended mainly for live paper trading.

        Uses the latest price to determine whether
        Take Profit or Stop Loss has been reached.
        """

        if price <= 0:
            raise ValueError(
                "Price must be greater than 0."
            )

        self.last_price = price

        # ----------------------------------------------------
        # NO OPEN POSITION
        # ----------------------------------------------------

        if self.position is None:

            return {
                "position_open": False,
                "closed": False,
                "reason":
                    "No open position.",
            }

        position = (
            self.position
        )

        # ----------------------------------------------------
        # LONG TAKE PROFIT
        # ----------------------------------------------------

        if (
            position.side == "LONG"
            and price
            >= position.take_profit
        ):

            return self.close_position(
                price=position.take_profit,
                reason="TAKE_PROFIT",
            )

        # ----------------------------------------------------
        # LONG STOP LOSS
        # ----------------------------------------------------

        if (
            position.side == "LONG"
            and price
            <= position.stop_loss
        ):

            return self.close_position(
                price=position.stop_loss,
                reason="STOP_LOSS",
            )

        # ----------------------------------------------------
        # POSITION REMAINS OPEN
        # ----------------------------------------------------

        return {
            "position_open": True,
            "closed": False,
            "unrealized_pnl":
                self.unrealized_pnl(),
        }

    # ========================================================
    # OHLC CANDLE UPDATE
    # ========================================================

    def update_candle(
        self,
        candle: dict,
    ) -> dict:
        """
        Check an open position against a completed
        OHLC candle.

        Intended mainly for backtesting.

        LONG position logic:

            high >= take_profit
                -> Take Profit hit

            low <= stop_loss
                -> Stop Loss hit

        If BOTH TP and SL are reached in the same candle,
        OHLC data cannot tell which happened first.

        Conservative assumption:
            STOP LOSS happened first.
        """

        # ----------------------------------------------------
        # VALIDATE REQUIRED FIELDS
        # ----------------------------------------------------

        required = {
            "high",
            "low",
            "close",
        }

        missing = [
            field
            for field in required
            if field not in candle
        ]

        if missing:

            raise ValueError(
                f"Missing candle fields: {missing}"
            )

        high_price = float(
            candle["high"]
        )

        low_price = float(
            candle["low"]
        )

        close_price = float(
            candle["close"]
        )

        if high_price <= 0:
            raise ValueError(
                "Candle high must be greater than 0."
            )

        if low_price <= 0:
            raise ValueError(
                "Candle low must be greater than 0."
            )

        if close_price <= 0:
            raise ValueError(
                "Candle close must be greater than 0."
            )

        if low_price > high_price:
            raise ValueError(
                "Candle low cannot be greater than high."
            )

        # ----------------------------------------------------
        # USE CANDLE CLOSE AS LAST PRICE
        # ----------------------------------------------------

        self.last_price = (
            close_price
        )

        # ----------------------------------------------------
        # NO OPEN POSITION
        # ----------------------------------------------------

        if self.position is None:

            return {
                "position_open": False,
                "closed": False,
                "reason":
                    "No open position.",
            }

        position = (
            self.position
        )

        # ====================================================
        # LONG POSITION
        # ====================================================

        if position.side == "LONG":

            stop_hit = (
                low_price
                <= position.stop_loss
            )

            take_profit_hit = (
                high_price
                >= position.take_profit
            )

            # ------------------------------------------------
            # BOTH HIT IN SAME CANDLE
            # ------------------------------------------------

            if (
                stop_hit
                and take_profit_hit
            ):

                logger.warning(
                    "BACKTEST | Both STOP LOSS and "
                    "TAKE PROFIT hit in same candle | "
                    "Using conservative STOP LOSS assumption."
                )

                return self.close_position(
                    price=position.stop_loss,
                    reason="STOP_LOSS",
                )

            # ------------------------------------------------
            # STOP LOSS HIT
            # ------------------------------------------------

            if stop_hit:

                return self.close_position(
                    price=position.stop_loss,
                    reason="STOP_LOSS",
                )

            # ------------------------------------------------
            # TAKE PROFIT HIT
            # ------------------------------------------------

            if take_profit_hit:

                return self.close_position(
                    price=position.take_profit,
                    reason="TAKE_PROFIT",
                )

        # ----------------------------------------------------
        # POSITION REMAINS OPEN
        # ----------------------------------------------------

        return {
            "position_open": True,
            "closed": False,
            "unrealized_pnl":
                self.unrealized_pnl(),
        }

    # ========================================================
    # CLOSE POSITION
    # ========================================================

    def close_position(
        self,
        price: float,
        reason: str = "MANUAL",
    ) -> dict:
        """
        Close the current paper position.
        """

        if self.position is None:

            return {
                "success": False,
                "closed": False,
                "reason":
                    "No open position.",
            }

        if price <= 0:

            return {
                "success": False,
                "closed": False,
                "reason":
                    "Exit price must be greater than 0.",
            }

        position = (
            self.position
        )

        # ----------------------------------------------------
        # EXIT VALUE
        # ----------------------------------------------------

        exit_value = (
            position.quantity
            * price
        )

        # ----------------------------------------------------
        # EXIT FEE
        # ----------------------------------------------------

        exit_fee = (
            exit_value
            * self.fee_rate
        )

        # ----------------------------------------------------
        # GROSS P&L
        # ----------------------------------------------------

        gross_pnl = (
            price
            - position.entry_price
        ) * position.quantity

        # ----------------------------------------------------
        # TOTAL FEES
        # ----------------------------------------------------

        total_fees = (
            position.fees_paid
            + exit_fee
        )

        # ----------------------------------------------------
        # NET P&L
        # ----------------------------------------------------

        net_pnl = (
            gross_pnl
            - total_fees
        )

        # ----------------------------------------------------
        # RETURN SALE PROCEEDS TO CASH
        # ----------------------------------------------------

        self.cash += (
            exit_value
            - exit_fee
        )

        # ----------------------------------------------------
        # REALIZED P&L
        # ----------------------------------------------------

        self.realized_pnl += (
            net_pnl
        )

        now = datetime.now(
            timezone.utc
        )

        # ----------------------------------------------------
        # TRADE HISTORY
        # ----------------------------------------------------

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

        self.trade_history.append(
            trade
        )

        # ----------------------------------------------------
        # CLEAR POSITION
        # ----------------------------------------------------

        self.position = None

        self.last_price = (
            price
        )

        logger.info(
            "PAPER SELL | %s | "
            "price=%.2f | "
            "gross_pnl=%.4f | "
            "fees=%.4f | "
            "net_pnl=%.4f | "
            "reason=%s",
            self.symbol,
            price,
            gross_pnl,
            total_fees,
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

    # ========================================================
    # UNREALIZED P&L
    # ========================================================

    def unrealized_pnl(
        self,
    ) -> float:
        """
        Return current unrealized P&L.
        """

        if self.position is None:
            return 0.0

        if self.last_price is None:
            return 0.0

        position = (
            self.position
        )

        if position.side == "LONG":

            return (
                self.last_price
                - position.entry_price
            ) * position.quantity

        return 0.0

    # ========================================================
    # POSITION VALUE
    # ========================================================

    def position_value(
        self,
    ) -> float:
        """
        Current market value of the open position.
        """

        if self.position is None:
            return 0.0

        if self.last_price is None:
            return 0.0

        return (
            self.position.quantity
            * self.last_price
        )

    # ========================================================
    # EQUITY
    # ========================================================

    def equity(
        self,
    ) -> float:
        """
        Equity = Cash + Current Position Value.
        """

        if self.position is None:

            return self.cash

        return (
            self.cash
            + self.position_value()
        )

    # ========================================================
    # TOTAL RETURN
    # ========================================================

    def total_return(
        self,
    ) -> float:
        """
        Total account P&L since starting balance.
        """

        return (
            self.equity()
            - self.starting_balance
        )

    # ========================================================
    # POSITION STATUS
    # ========================================================

    def get_position(
        self,
    ) -> Optional[dict]:
        """
        Return current open position.
        """

        if self.position is None:

            return None

        position = (
            self.position
        )

        return {
            "symbol":
                position.symbol,

            "side":
                position.side,

            "quantity":
                position.quantity,

            "entry_price":
                position.entry_price,

            "stop_loss":
                position.stop_loss,

            "take_profit":
                position.take_profit,

            "entry_fee":
                position.fees_paid,

            "current_price":
                self.last_price,

            "position_value":
                self.position_value(),

            "unrealized_pnl":
                self.unrealized_pnl(),
        }

    # ========================================================
    # ACCOUNT STATUS
    # ========================================================

    def account_status(
        self,
    ) -> dict:
        """
        Return current paper account status.
        """

        return {
            "starting_balance":
                self.starting_balance,

            "cash":
                self.cash,

            "equity":
                self.equity(),

            "realized_pnl":
                self.realized_pnl,

            "unrealized_pnl":
                self.unrealized_pnl(),

            "total_return":
                self.total_return(),

            "open_position":
                self.get_position(),

            "total_trades":
                len(
                    self.trade_history
                ),
        }
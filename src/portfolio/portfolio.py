import logging
from typing import Optional


logger = logging.getLogger(__name__)


class Portfolio:
    """
    Tracks paper-trading account state.

    The Portfolio does not generate signals and does not
    communicate with an exchange.
    """

    def __init__(
        self,
        starting_balance: float = 1000.0,
    ):
        if starting_balance <= 0:
            raise ValueError(
                "Starting balance must be greater than 0."
            )

        self.starting_balance = starting_balance
        self.cash = starting_balance

        self.quantity = 0.0
        self.entry_price: Optional[float] = None
        self.current_price: Optional[float] = None

        self.realized_pnl = 0.0
        self.total_fees = 0.0

        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def open_position(
        self,
        quantity: float,
        price: float,
        fee: float = 0.0,
    ) -> bool:

        if quantity <= 0:
            return False

        if price <= 0:
            return False

        position_value = quantity * price
        total_cost = position_value + fee

        if total_cost > self.cash:
            return False

        self.cash -= total_cost

        self.quantity = quantity
        self.entry_price = price
        self.current_price = price

        self.total_fees += fee

        logger.info(
            "Portfolio position opened: %.8f ETH @ %.2f",
            quantity,
            price,
        )

        return True

    def update_price(
        self,
        price: float,
    ):

        if price <= 0:
            return

        self.current_price = price

    def close_position(
        self,
        price: float,
        fee: float = 0.0,
    ) -> Optional[float]:

        if self.quantity <= 0:
            return None

        if price <= 0:
            return None

        gross_pnl = (
            price - self.entry_price
        ) * self.quantity

        position_value = (
            self.quantity * price
        )

        net_pnl = (
            gross_pnl - fee
        )

        self.cash += (
            position_value - fee
        )

        self.realized_pnl += net_pnl
        self.total_fees += fee

        self.total_trades += 1

        if net_pnl > 0:
            self.winning_trades += 1
        elif net_pnl < 0:
            self.losing_trades += 1

        self.quantity = 0.0
        self.entry_price = None

        return net_pnl

    def unrealized_pnl(self) -> float:

        if self.quantity <= 0:
            return 0.0

        if self.entry_price is None:
            return 0.0

        if self.current_price is None:
            return 0.0

        return (
            self.current_price
            - self.entry_price
        ) * self.quantity

    def position_value(self) -> float:

        if self.quantity <= 0:
            return 0.0

        if self.current_price is None:
            return 0.0

        return (
            self.quantity
            * self.current_price
        )

    def equity(self) -> float:

        return (
            self.cash
            + self.position_value()
        )

    def total_pnl(self) -> float:

        return (
            self.equity()
            - self.starting_balance
        )

    def win_rate(self) -> float:

        if self.total_trades == 0:
            return 0.0

        return (
            self.winning_trades
            / self.total_trades
        )

    def has_position(self) -> bool:

        return self.quantity > 0

    def status(self) -> dict:

        return {
            "starting_balance":
                self.starting_balance,

            "cash":
                self.cash,

            "position_quantity":
                self.quantity,

            "entry_price":
                self.entry_price,

            "current_price":
                self.current_price,

            "position_value":
                self.position_value(),

            "realized_pnl":
                self.realized_pnl,

            "unrealized_pnl":
                self.unrealized_pnl(),

            "total_pnl":
                self.total_pnl(),

            "equity":
                self.equity(),

            "total_fees":
                self.total_fees,

            "total_trades":
                self.total_trades,

            "winning_trades":
                self.winning_trades,

            "losing_trades":
                self.losing_trades,

            "win_rate":
                self.win_rate(),
        }
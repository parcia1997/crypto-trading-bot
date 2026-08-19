import logging
from typing import Optional

from src.risk.risk_engine import RiskEngine
from src.execution.paper import PaperExecutionEngine
from src.portfolio.portfolio import Portfolio


logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Connects:

        Strategy
            ↓
        Risk Engine
            ↓
        Paper Execution
            ↓
        Portfolio

    PAPER TRADING ONLY.
    """

    def __init__(
        self,
        starting_balance: float = 1000.0,
        risk_per_trade: float = 0.01,
        fee_rate: float = 0.001,
        symbol: str = "ETHUSDT",
    ):
        self.symbol = symbol.upper()

        self.risk_engine = RiskEngine(
            account_balance=starting_balance,
            risk_per_trade=risk_per_trade,
        )

        self.execution = PaperExecutionEngine(
            starting_balance=starting_balance,
            fee_rate=fee_rate,
            symbol=self.symbol,
        )

        self.portfolio = Portfolio(
            starting_balance=starting_balance
        )

    # --------------------------------------------------
    # PROCESS STRATEGY SIGNAL
    # --------------------------------------------------

    def process_signal(
        self,
        signal: dict,
    ) -> dict:

        action = signal.get("action")

        logger.info(
            "Strategy signal: %s",
            action,
        )

        # --------------------------------------------------
        # HOLD
        # --------------------------------------------------

        if action == "HOLD":

            return {
                "action": "HOLD",
                "executed": False,
                "reason": "Strategy returned HOLD.",
            }

        # --------------------------------------------------
        # Don't open another position
        # --------------------------------------------------

        if self.portfolio.has_position():

            return {
                "action": action,
                "executed": False,
                "reason": (
                    "A position is already open."
                ),
            }

        # --------------------------------------------------
        # Risk calculation
        # --------------------------------------------------

        risk_result = (
            self.risk_engine.evaluate(
                signal
            )
        )

        if not risk_result["approved"]:

            logger.info(
                "Trade rejected by risk engine."
            )

            return {
                "action": action,
                "executed": False,
                "reason": risk_result[
                    "reason"
                ],
                "risk": risk_result,
            }

        # --------------------------------------------------
        # BUY
        # --------------------------------------------------

        if action == "BUY":

            quantity = (
                risk_result[
                    "position_size"
                ]
            )

            entry_price = (
                risk_result[
                    "entry_price"
                ]
            )

            stop_loss = (
                risk_result[
                    "stop_loss"
                ]
            )

            take_profit = (
                risk_result[
                    "take_profit"
                ]
            )

            # Paper execution

            execution_result = (
                self.execution.open_long(
                    quantity=quantity,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
            )

            if not execution_result[
                "success"
            ]:

                return {
                    "action": action,
                    "executed": False,
                    "reason": execution_result[
                        "reason"
                    ],
                }

            # Portfolio

            portfolio_result = (
                self.portfolio.open_position(
                    quantity=quantity,
                    price=entry_price,
                    fee=execution_result[
                        "fee"
                    ],
                )
            )

            if not portfolio_result:

                # Safety check.

                self.execution.close_position(
                    price=entry_price,
                    reason="PORTFOLIO_REJECTED",
                )

                return {
                    "action": action,
                    "executed": False,
                    "reason": (
                        "Portfolio rejected "
                        "the position."
                    ),
                }

            logger.info(
                "PAPER BUY EXECUTED | "
                "quantity=%.8f | price=%.2f",
                quantity,
                entry_price,
            )

            return {
                "action": "BUY",
                "executed": True,
                "quantity": quantity,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk": risk_result,
            }

        # --------------------------------------------------
        # SELL
        # --------------------------------------------------

        if action == "SELL":

            return self._process_sell(
                signal
            )

        return {
            "action": action,
            "executed": False,
            "reason": "Unsupported action.",
        }

    # --------------------------------------------------
    # SELL
    # --------------------------------------------------

    def _process_sell(
        self,
        signal: dict,
    ) -> dict:

        # This first version only supports
        # closing an existing LONG position.

        if not self.portfolio.has_position():

            return {
                "action": "SELL",
                "executed": False,
                "reason": (
                    "No LONG position to close."
                ),
            }

        price = self._get_price(
            signal
        )

        if price is None:

            return {
                "action": "SELL",
                "executed": False,
                "reason": "Invalid price.",
            }

        return self.close_position(
            price=price,
            reason="STRATEGY_SELL",
        )

    # --------------------------------------------------
    # UPDATE MARKET PRICE
    # --------------------------------------------------

    def update_price(
        self,
        price: float,
    ) -> dict:

        if price <= 0:

            return {
                "success": False,
                "reason": "Invalid price.",
            }

        self.portfolio.update_price(
            price
        )

        result = (
            self.execution.update_price(
                price
            )
        )

        # Position was closed by SL/TP.

        if result.get("closed"):

            close_result = (
                self.portfolio.close_position(
                    price=result[
                        "exit_price"
                    ],
                    fee=self._calculate_exit_fee(
                        result[
                            "exit_price"
                        ]
                    ),
                )
            )

            return {
                "closed": True,
                "reason": result[
                    "reason"
                ],
                "net_pnl": close_result,
                "price": result[
                    "exit_price"
                ],
            }

        return {
            "closed": False,
            "unrealized_pnl":
                self.portfolio.unrealized_pnl(),
        }

    # --------------------------------------------------
    # MANUAL CLOSE
    # --------------------------------------------------

    def close_position(
        self,
        price: float,
        reason: str = "MANUAL",
    ) -> dict:

        if not self.portfolio.has_position():

            return {
                "success": False,
                "reason": "No open position.",
            }

        execution_result = (
            self.execution.close_position(
                price=price,
                reason=reason,
            )
        )

        if not execution_result[
            "success"
        ]:

            return execution_result

        net_pnl = (
            self.portfolio.close_position(
                price=price,
                fee=self._calculate_exit_fee(
                    price
                ),
            )
        )

        return {
            "success": True,
            "price": price,
            "net_pnl": net_pnl,
            "reason": reason,
        }

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def status(self) -> dict:

        return self.portfolio.status()

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def _calculate_exit_fee(
        self,
        price: float,
    ) -> float:

        quantity = self.portfolio.quantity

        return (
            quantity
            * price
            * self.execution.fee_rate
        )

    @staticmethod
    def _get_price(
        signal: dict,
    ) -> Optional[float]:

        price = signal.get(
            "price"
        )

        try:

            return float(price)

        except (
            TypeError,
            ValueError,
        ):

            return None
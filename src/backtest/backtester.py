import logging

from src.bot.trading_bot import TradingBot
from src.backtest.metrics import BacktestMetrics


logger = logging.getLogger(__name__)


class Backtester:
    """
    Replays historical candles through the TradingBot.

    Uses the same:
        - strategy
        - risk engine
        - fee assumptions
        - paper execution
        - portfolio logic

    as the live paper-trading system.
    """

    def __init__(
        self,
        symbol: str = "ETHUSDT",
        starting_balance: float = 1000.0,
        warmup_candles: int = 50,
    ):
        self.symbol = symbol
        self.starting_balance = starting_balance
        self.warmup_candles = warmup_candles

        self.bot = TradingBot(
            symbol=symbol,
            starting_balance=starting_balance,
        )

        self.equity_curve = []

    def run(
        self,
        candles: list[dict],
    ) -> dict:
        """
        Run the backtest.
        """

        if len(candles) <= self.warmup_candles:
            raise ValueError(
                "Not enough candles for backtesting."
            )

        self.bot.start()

        # ------------------------------------------
        # Warm-up history
        # ------------------------------------------

        warmup = candles[
            :self.warmup_candles
        ]

        self.bot.load_historical_candles(
            warmup
        )

        # ------------------------------------------
        # Replay candles one by one
        # ------------------------------------------

        for candle in candles[
            self.warmup_candles:
        ]:

            self.bot.process_candle(
                candle
            )

            equity = (
                self.bot.paper_engine.equity()
            )

            self.equity_curve.append(
                equity
            )

        # ------------------------------------------
        # Close any remaining position
        # ------------------------------------------

        if (
            self.bot.paper_engine.position
            is not None
        ):

            last_price = float(
                candles[-1]["close"]
            )

            result = (
                self.bot.paper_engine.close_position(
                    price=last_price,
                    reason="BACKTEST_END",
                )
            )

            if result.get("success"):
                self.bot._sync_portfolio_after_close()

        self.bot.stop()

        # ------------------------------------------
        # Metrics
        # ------------------------------------------

        ending_equity = (
            self.bot.paper_engine.equity()
        )

        trades = (
            self.bot.paper_engine.trade_history
        )

        metrics = (
            BacktestMetrics.calculate(
                trades=trades,
                starting_balance=self.starting_balance,
                ending_equity=ending_equity,
            )
        )

        metrics["starting_balance"] = (
            self.starting_balance
        )

        metrics["ending_equity"] = (
            ending_equity
        )

        metrics["candles_tested"] = (
            len(candles)
        )

        metrics["signals_buy"] = (
            self.bot.buy_signals
        )

        metrics["signals_sell"] = (
            self.bot.sell_signals
        )

        metrics["signals_hold"] = (
            self.bot.hold_signals
        )

        metrics["rejected_trades"] = (
            self.bot.rejected_trades
        )

        return metrics
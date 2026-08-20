import logging
from collections import Counter

from src.bot.trading_bot import TradingBot
from src.backtest.metrics import BacktestMetrics


logger = logging.getLogger(__name__)


class Backtester:
    """
    Replays historical candles through TradingBot.

    Tracks:
        - Trades
        - Equity
        - Signals
        - Rejected trades
        - Rejection reasons
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

        self.rejection_reasons = Counter()

    # ==================================================
    # RUN BACKTEST
    # ==================================================

    def run(
        self,
        candles: list[dict],
    ) -> dict:

        if len(candles) <= self.warmup_candles:

            raise ValueError(
                "Not enough candles for backtesting."
            )

        self.bot.start()

        # --------------------------------------------------
        # WARM-UP
        # --------------------------------------------------

        warmup = candles[
            :self.warmup_candles
        ]

        self.bot.load_historical_candles(
            warmup
        )

        # --------------------------------------------------
        # REPLAY CANDLES
        # --------------------------------------------------

        for candle in candles[
            self.warmup_candles:
        ]:

            result = (
                self.bot.process_candle(
                    candle
                )
            )

            # ----------------------------------------------
            # TRACK REJECTION REASONS
            # ----------------------------------------------

            if (
                result.get("executed") is False
                and result.get("risk")
                and not result["risk"].get(
                    "approved",
                    False,
                )
            ):

                reasons = (
                    result["risk"].get(
                        "reason",
                        [],
                    )
                )

                for reason in reasons:

                    self._record_rejection_reason(
                        reason
                    )

            # ----------------------------------------------
            # EQUITY CURVE
            # ----------------------------------------------

            equity = (
                self.bot.paper_engine.equity()
            )

            self.equity_curve.append(
                equity
            )

        # --------------------------------------------------
        # CLOSE OPEN POSITION AT END
        # --------------------------------------------------

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

        # --------------------------------------------------
        # FINAL EQUITY
        # --------------------------------------------------

        ending_equity = (
            self.bot.paper_engine.equity()
        )

        # --------------------------------------------------
        # TRADE HISTORY
        # --------------------------------------------------

        trades = (
            self.bot.paper_engine.trade_history
        )

        # --------------------------------------------------
        # METRICS
        # --------------------------------------------------

        metrics = (
            BacktestMetrics.calculate(
                trades=trades,
                starting_balance=self.starting_balance,
                ending_equity=ending_equity,
            )
        )

        # --------------------------------------------------
        # EXTRA BACKTEST DATA
        # --------------------------------------------------

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

        metrics["rejection_reasons"] = dict(
            self.rejection_reasons
        )

        metrics["equity_curve"] = (
            self.equity_curve
        )

        return metrics

    # ==================================================
    # REJECTION ANALYSIS
    # ==================================================

    def _record_rejection_reason(
        self,
        reason: str,
    ):
        """
        Convert detailed RiskEngine messages
        into simple rejection categories.
        """

        if not reason:

            self.rejection_reasons[
                "UNKNOWN"
            ] += 1

            return

        text = reason.lower()

        # --------------------------------------------------
        # Expected net return too small
        # --------------------------------------------------

        if (
            "expected net return is too small"
            in text
        ):

            category = (
                "NET_RETURN_TOO_SMALL"
            )

        # --------------------------------------------------
        # Profit doesn't cover fees/slippage
        # --------------------------------------------------

        elif (
            "expected profit does not cover"
            in text
            or
            "expected net profit is too small"
            in text
        ):

            category = (
                "NET_PROFIT_TOO_SMALL"
            )

        # --------------------------------------------------
        # Risk/reward
        # --------------------------------------------------

        elif "risk/reward" in text:

            category = (
                "RISK_REWARD_TOO_LOW"
            )

        # --------------------------------------------------
        # ATR
        # --------------------------------------------------

        elif (
            "atr is not available"
            in text
        ):

            category = (
                "ATR_MISSING"
            )

        # --------------------------------------------------
        # Position size
        # --------------------------------------------------

        elif (
            "position size is too small"
            in text
        ):

            category = (
                "POSITION_TOO_SMALL"
            )

        # --------------------------------------------------
        # Entry price
        # --------------------------------------------------

        elif (
            "invalid entry price"
            in text
        ):

            category = (
                "INVALID_ENTRY_PRICE"
            )

        # --------------------------------------------------
        # Stop loss
        # --------------------------------------------------

        elif (
            "stop-loss"
            in text
        ):

            category = (
                "STOP_LOSS_INVALID"
            )

        # --------------------------------------------------
        # Take profit
        # --------------------------------------------------

        elif (
            "take-profit"
            in text
        ):

            category = (
                "TAKE_PROFIT_INVALID"
            )

        # --------------------------------------------------
        # Everything else
        # --------------------------------------------------

        else:

            category = "OTHER"

        self.rejection_reasons[
            category
        ] += 1
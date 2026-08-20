import logging
from collections import Counter

from src.bot.trading_bot import TradingBot
from src.backtest.metrics import BacktestMetrics
from src.database.repository import TradingRepository


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

    Database behavior:

        TradingBot database writes:
            DISABLED during replay

        Backtest summary:
            Can be saved once to PostgreSQL
            after the backtest completes
    """

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        symbol: str = "ETHUSDT",
        starting_balance: float = 1000.0,
        warmup_candles: int = 50,

        # Backtest metadata
        timeframe: str = "1m",

        # Save one summary row into PostgreSQL
        save_result_to_database: bool = False,
    ):

        self.symbol = symbol.upper()

        self.starting_balance = (
            starting_balance
        )

        self.warmup_candles = (
            warmup_candles
        )

        self.timeframe = (
            timeframe
        )

        self.save_result_to_database = (
            save_result_to_database
        )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # Database disabled inside TradingBot.
        #
        # We do NOT want thousands of backtest candles
        # and signals written into live PostgreSQL tables.
        # --------------------------------------------------

        self.bot = TradingBot(
            symbol=self.symbol,
            starting_balance=self.starting_balance,
            enable_database=False,
        )

        # --------------------------------------------------
        # Repository used ONLY for backtest summary.
        # --------------------------------------------------

        self.repository = None

        if self.save_result_to_database:

            self.repository = (
                TradingRepository()
            )

        # --------------------------------------------------
        # Backtest tracking
        # --------------------------------------------------

        self.equity_curve = []

        self.rejection_reasons = (
            Counter()
        )

    # ==================================================
    # RUN BACKTEST
    # ==================================================

    def run(
        self,
        candles: list[dict],
    ) -> dict:

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if len(candles) <= self.warmup_candles:

            raise ValueError(
                "Not enough candles for backtesting."
            )

        # Reset state in case same Backtester object
        # is ever reused.
        self.equity_curve = []

        self.rejection_reasons.clear()

        # --------------------------------------------------
        # START BOT
        # --------------------------------------------------

        self.bot.start()

        # ==================================================
        # WARM-UP
        # ==================================================

        warmup = candles[
            :self.warmup_candles
        ]

        self.bot.load_historical_candles(
            warmup
        )

        # ==================================================
        # REPLAY CANDLES
        # ==================================================

        for candle in candles[
            self.warmup_candles:
        ]:

            result = (
                self.bot.process_candle(
                    candle,
                    use_ohlc_execution=True,
                )
            )

            # ----------------------------------------------
            # TRACK REJECTION REASONS
            # ----------------------------------------------

            if (
                result.get(
                    "executed"
                ) is False

                and result.get(
                    "risk"
                )

                and not result[
                    "risk"
                ].get(
                    "approved",
                    False,
                )
            ):

                reasons = (
                    result[
                        "risk"
                    ].get(
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
                self.bot
                .paper_engine
                .equity()
            )

            self.equity_curve.append(
                equity
            )

        # ==================================================
        # CLOSE OPEN POSITION AT END
        # ==================================================

        if (
            self.bot
            .paper_engine
            .position
            is not None
        ):

            last_price = float(
                candles[-1][
                    "close"
                ]
            )

            close_result = (
                self.bot
                .paper_engine
                .close_position(
                    price=last_price,
                    reason="BACKTEST_END",
                )
            )

            if close_result.get(
                "success"
            ):

                self.bot._sync_portfolio_after_close()

        # ==================================================
        # STOP BOT
        # ==================================================

        self.bot.stop()

        # ==================================================
        # FINAL EQUITY
        # ==================================================

        ending_equity = (
            self.bot
            .paper_engine
            .equity()
        )

        # ==================================================
        # TRADE HISTORY
        # ==================================================

        trades = (
            self.bot
            .paper_engine
            .trade_history
        )

        # ==================================================
        # METRICS
        # ==================================================

        metrics = (
            BacktestMetrics.calculate(
                trades=trades,
                starting_balance=(
                    self.starting_balance
                ),
                ending_equity=(
                    ending_equity
                ),
            )
        )

        # ==================================================
        # EXTRA BACKTEST DATA
        # ==================================================

        metrics[
            "symbol"
        ] = self.symbol

        metrics[
            "timeframe"
        ] = self.timeframe

        metrics[
            "starting_balance"
        ] = self.starting_balance

        metrics[
            "ending_equity"
        ] = ending_equity

        # Repository currently expects key:
        # "candles"
        metrics[
            "candles"
        ] = len(candles)

        # Keep this too because your existing
        # scripts may already use it.
        metrics[
            "candles_tested"
        ] = len(candles)

        metrics[
            "warmup_candles"
        ] = (
            self.warmup_candles
        )

        metrics[
            "signals_buy"
        ] = (
            self.bot.buy_signals
        )

        metrics[
            "signals_sell"
        ] = (
            self.bot.sell_signals
        )

        metrics[
            "signals_hold"
        ] = (
            self.bot.hold_signals
        )

        metrics[
            "rejected_trades"
        ] = (
            self.bot.rejected_trades
        )

        metrics[
            "rejection_reasons"
        ] = dict(
            self.rejection_reasons
        )

        metrics[
            "equity_curve"
        ] = (
            self.equity_curve
        )

        # ==================================================
        # SAVE ONE SUMMARY ROW TO POSTGRESQL
        # ==================================================

        if (
            self.save_result_to_database
            and self.repository is not None
        ):

            backtest_id = (
                self.repository
                .save_backtest_run(
                    result=metrics,
                    timeframe=self.timeframe,
                )
            )

            metrics[
                "backtest_id"
            ] = backtest_id

            if backtest_id is not None:

                logger.info(
                    "DATABASE | "
                    "Backtest result saved | "
                    "id=%s | "
                    "timeframe=%s | "
                    "net_profit=%.4f",
                    backtest_id,
                    self.timeframe,
                    metrics[
                        "net_profit"
                    ],
                )

            else:

                logger.error(
                    "DATABASE | "
                    "Failed to save backtest result."
                )

        else:

            metrics[
                "backtest_id"
            ] = None

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

        text = (
            reason.lower()
        )

        # --------------------------------------------------
        # NET RETURN TOO SMALL
        # --------------------------------------------------

        if (
            "expected net return is too small"
            in text
        ):

            category = (
                "NET_RETURN_TOO_SMALL"
            )

        # --------------------------------------------------
        # PROFIT DOESN'T COVER FEES / SLIPPAGE
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
        # RISK / REWARD
        # --------------------------------------------------

        elif (
            "risk/reward"
            in text
        ):

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
        # POSITION SIZE
        # --------------------------------------------------

        elif (
            "position size is too small"
            in text
        ):

            category = (
                "POSITION_TOO_SMALL"
            )

        # --------------------------------------------------
        # ENTRY PRICE
        # --------------------------------------------------

        elif (
            "invalid entry price"
            in text
        ):

            category = (
                "INVALID_ENTRY_PRICE"
            )

        # --------------------------------------------------
        # STOP LOSS
        # --------------------------------------------------

        elif (
            "stop-loss"
            in text
        ):

            category = (
                "STOP_LOSS_INVALID"
            )

        # --------------------------------------------------
        # TAKE PROFIT
        # --------------------------------------------------

        elif (
            "take-profit"
            in text
        ):

            category = (
                "TAKE_PROFIT_INVALID"
            )

        # --------------------------------------------------
        # OTHER
        # --------------------------------------------------

        else:

            category = (
                "OTHER"
            )

        self.rejection_reasons[
            category
        ] += 1
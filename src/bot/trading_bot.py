import logging
from typing import Optional

from src.market.candle_store import CandleStore
from src.strategy.strategy import TradingStrategy
from src.risk.risk_engine import RiskEngine
from src.execution.paper import PaperExecutionEngine
from src.portfolio.portfolio import Portfolio


logger = logging.getLogger(__name__)


class TradingBot:
    """
    Main trading bot controller.

    Connects:

        CandleStore
            ↓
        TradingStrategy
            ↓
        RiskEngine
            ↓
        PaperExecutionEngine
            ↓
        Portfolio

    IMPORTANT:
    This version is PAPER TRADING ONLY.
    It does not send real orders to Binance.
    """

    def __init__(
        self,
        symbol: str = "ETHUSDT",
        starting_balance: float = 1000.0,
        max_candles: int = 2000,
        minimum_candles: int = 50,
        volume_threshold: float = 1.0,
        risk_per_trade: float = 0.01,
        stop_loss_atr_multiplier: float = 1.0,
        take_profit_atr_multiplier: float = 2.0,
        max_position_percentage: float = 0.25,
        fee_rate: float = 0.001,
    ):
        self.symbol = symbol.upper()

        self.starting_balance = starting_balance

        # --------------------------------------------------
        # MARKET DATA
        # --------------------------------------------------

        self.candle_store = CandleStore(
            max_candles=max_candles
        )

        # --------------------------------------------------
        # STRATEGY
        # --------------------------------------------------

        self.strategy = TradingStrategy(
            minimum_candles=minimum_candles,
            volume_threshold=volume_threshold,
        )

        # --------------------------------------------------
        # RISK
        # --------------------------------------------------

        self.risk_engine = RiskEngine(
            account_balance=starting_balance,
            risk_per_trade=risk_per_trade,
            stop_loss_atr_multiplier=stop_loss_atr_multiplier,
            take_profit_atr_multiplier=take_profit_atr_multiplier,
            max_position_percentage=max_position_percentage,
        )

        # --------------------------------------------------
        # PAPER EXECUTION
        # --------------------------------------------------

        self.paper_engine = PaperExecutionEngine(
            starting_balance=starting_balance,
            fee_rate=fee_rate,
            symbol=self.symbol,
        )

        # --------------------------------------------------
        # PORTFOLIO
        # --------------------------------------------------

        self.portfolio = Portfolio(
            starting_balance=starting_balance
        )

        # --------------------------------------------------
        # STATISTICS
        # --------------------------------------------------

        self.candles_processed = 0
        self.buy_signals = 0
        self.sell_signals = 0
        self.hold_signals = 0
        self.rejected_trades = 0

        self.running = False

    # ======================================================
    # CANDLE PROCESSING
    # ======================================================

    def process_candle(
        self,
        candle: dict,
    ) -> dict:
        """
        Process one completed candle.

        Flow:

            Candle
              ↓
            Store
              ↓
          Strategy
              ↓
            Risk
              ↓
           Execute
              ↓
          Portfolio
        """

        self.candles_processed += 1

        logger.info(
            "Processing candle #%s | %s | close=%.2f",
            self.candles_processed,
            candle.get("timestamp"),
            candle.get("close"),
        )

        # --------------------------------------------------
        # STORE CANDLE
        # --------------------------------------------------

        added = self.candle_store.add(
            candle
        )

        if not added:

            return {
                "action": "HOLD",
                "reason": "Invalid candle.",
            }

        candles = self.candle_store.get_all()

        # --------------------------------------------------
        # STRATEGY
        # --------------------------------------------------

        signal = self.strategy.generate_signal(
            candles
        )

        action = signal.get(
            "action",
            "HOLD",
        )

        confidence = signal.get(
            "confidence",
            0.0,
        )

        logger.info(
            "STRATEGY | action=%s | confidence=%.2f | reason=%s",
            action,
            confidence,
            signal.get("reason"),
        )

        # --------------------------------------------------
        # SIGNAL STATISTICS
        # --------------------------------------------------

        if action == "BUY":
            self.buy_signals += 1

        elif action == "SELL":
            self.sell_signals += 1

        else:
            self.hold_signals += 1

        # --------------------------------------------------
        # UPDATE CURRENT PAPER POSITION
        # --------------------------------------------------

        market_price = float(
            candle["close"]
        )

        execution_update = (
            self.paper_engine.update_price(
                market_price
            )
        )

        # --------------------------------------------------
        # POSITION CLOSED
        # --------------------------------------------------

        if execution_update.get("closed"):

            logger.info(
                "POSITION CLOSED | %s",
                execution_update,
            )

            self._sync_portfolio_after_close()

        # --------------------------------------------------
        # DON'T OPEN ANOTHER POSITION
        # --------------------------------------------------

        if self.paper_engine.position is not None:

            logger.info(
                "POSITION OPEN | %s",
                self.paper_engine.get_position(),
            )

            return {
                "action": action,
                "executed": False,
                "position_open": True,
                "signal": signal,
                "execution": execution_update,
            }

        # --------------------------------------------------
        # ONLY BUY/SELL CONTINUE
        # --------------------------------------------------

        if action not in {
            "BUY",
            "SELL",
        }:

            return {
                "action": action,
                "executed": False,
                "signal": signal,
                "execution": execution_update,
            }

        # --------------------------------------------------
        # RISK ENGINE
        # --------------------------------------------------

        risk_result = self.risk_engine.evaluate(
            signal
        )

        logger.info(
            "RISK | approved=%s | action=%s | "
            "size=%.8f | SL=%s | TP=%s",
            risk_result["approved"],
            risk_result["action"],
            risk_result["position_size"],
            risk_result["stop_loss"],
            risk_result["take_profit"],
        )

        # --------------------------------------------------
        # TRADE REJECTED
        # --------------------------------------------------

        if not risk_result["approved"]:

            self.rejected_trades += 1

            logger.info(
                "TRADE REJECTED | %s",
                risk_result["reason"],
            )

            return {
                "action": action,
                "executed": False,
                "signal": signal,
                "risk": risk_result,
            }

        # --------------------------------------------------
        # PAPER BUY
        # --------------------------------------------------

        if risk_result["action"] == "BUY":

            return self._execute_buy(
                risk_result
            )

        # --------------------------------------------------
        # SELL
        # --------------------------------------------------

        if risk_result["action"] == "SELL":

            logger.info(
                "SELL signal received."
            )

            return {
                "action": "SELL",
                "executed": False,
                "reason": [
                    "SELL execution is not implemented "
                    "in the current long-only paper engine."
                ],
                "signal": signal,
                "risk": risk_result,
            }

        return {
            "action": action,
            "executed": False,
            "signal": signal,
            "risk": risk_result,
        }

    # ======================================================
    # BUY EXECUTION
    # ======================================================

    def _execute_buy(
        self,
        risk_result: dict,
    ) -> dict:
        """
        Execute an approved BUY using paper trading.
        """

        quantity = risk_result[
            "position_size"
        ]

        entry_price = risk_result[
            "entry_price"
        ]

        stop_loss = risk_result[
            "stop_loss"
        ]

        take_profit = risk_result[
            "take_profit"
        ]

        result = self.paper_engine.open_long(
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        logger.info(
            "PAPER EXECUTION | %s",
            result,
        )

        if not result.get("success"):

            logger.warning(
                "Paper execution failed | %s",
                result,
            )

            return {
                "action": "BUY",
                "executed": False,
                "reason": [
                    result.get(
                        "reason",
                        "Paper execution failed.",
                    )
                ],
                "risk": risk_result,
            }

        # --------------------------------------------------
        # UPDATE PORTFOLIO
        # --------------------------------------------------

        portfolio_result = (
            self.portfolio.open_position(
                quantity=quantity,
                price=entry_price,
                fee=result.get(
                    "fee",
                    0.0,
                ),
            )
        )

        if not portfolio_result:

            logger.error(
                "Portfolio update failed after "
                "successful paper execution."
            )

        return {
            "action": "BUY",
            "executed": True,
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": risk_result,
            "execution": result,
        }

    # ======================================================
    # PORTFOLIO CLOSE SYNC
    # ======================================================

    def _sync_portfolio_after_close(
        self,
    ):
        """
        Synchronize Portfolio after the paper
        execution engine closes a position.
        """

        trade_history = (
            self.paper_engine.trade_history
        )

        if not trade_history:
            return

        latest_trade = trade_history[-1]

        # Portfolio should have the same
        # position before closing.
        if not self.portfolio.has_position():

            logger.warning(
                "Portfolio has no position to close."
            )

            return

        self.portfolio.update_price(
            latest_trade.exit_price
        )

        portfolio_pnl = (
            self.portfolio.close_position(
                price=latest_trade.exit_price,
                fee=latest_trade.fees,
            )
        )

        logger.info(
            "PORTFOLIO CLOSED | net_pnl=%s",
            portfolio_pnl,
        )

    # ======================================================
    # STATUS
    # ======================================================

    def status(self) -> dict:
        """
        Return complete bot status.
        """

        account = (
            self.paper_engine.account_status()
        )

        portfolio = (
            self.portfolio.status()
        )

        return {
            "symbol": self.symbol,
            "running": self.running,

            "candles_processed":
                self.candles_processed,

            "candle_store_count":
                self.candle_store.count(),

            "buy_signals":
                self.buy_signals,

            "sell_signals":
                self.sell_signals,

            "hold_signals":
                self.hold_signals,

            "rejected_trades":
                self.rejected_trades,

            "account":
                account,

            "portfolio":
                portfolio,
        }

    # ======================================================
    # SUMMARY
    # ======================================================

    def summary(self) -> dict:
        """
        Compact trading summary.
        """

        account = (
            self.paper_engine.account_status()
        )

        return {
            "symbol": self.symbol,
            "balance": account["cash"],
            "equity": account["equity"],
            "realized_pnl": account[
                "realized_pnl"
            ],
            "unrealized_pnl": account[
                "unrealized_pnl"
            ],
            "total_return": account[
                "total_return"
            ],
            "trades": account[
                "total_trades"
            ],
            "candles": self.candles_processed,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
            "hold_signals": self.hold_signals,
        }

    # ======================================================
    # START / STOP
    # ======================================================

    def start(self):
        """
        Mark bot as running.
        """

        self.running = True

        logger.info(
            "TradingBot started | symbol=%s",
            self.symbol,
        )

    def stop(self):
        """
        Stop the bot.
        """

        self.running = False

        logger.info(
            "TradingBot stopped."
        )

        logger.info(
            "Final summary | %s",
            self.summary(),
        )
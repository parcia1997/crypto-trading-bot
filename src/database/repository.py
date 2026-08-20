import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from src.database.db import SessionLocal
from src.database.models import (
    AccountSnapshotModel,
    BacktestRunModel,
    CandleModel,
    SignalModel,
    TradeModel,
)


logger = logging.getLogger(__name__)


class TradingRepository:
    """
    Repository responsible for saving trading-bot
    data into PostgreSQL.

    Trading logic should not contain direct SQL code.
    """

    # ========================================================
    # SAVE CANDLE
    # ========================================================

    def save_candle(
        self,
        candle: dict,
        interval: str = "1m",
    ) -> Optional[int]:

        session = SessionLocal()

        try:

            record = CandleModel(
                timestamp=candle["timestamp"],
                symbol=candle["symbol"],
                interval=interval,
                open=float(candle["open"]),
                high=float(candle["high"]),
                low=float(candle["low"]),
                close=float(candle["close"]),
                volume=float(candle["volume"]),
                trade_count=int(
                    candle.get(
                        "trade_count",
                        0,
                    )
                ),
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record.id

        except SQLAlchemyError:

            session.rollback()

            logger.exception(
                "Failed to save candle."
            )

            return None

        finally:

            session.close()

    # ========================================================
    # SAVE SIGNAL
    # ========================================================

    def save_signal(
        self,
        signal: dict,
        candle: dict,
    ) -> Optional[int]:

        session = SessionLocal()

        try:

            reason = signal.get(
                "reason"
            )

            # Strategy currently returns reason as a list.
            # Store it as JSON text.
            if isinstance(
                reason,
                (list, dict),
            ):

                reason = json.dumps(
                    reason
                )

            elif reason is not None:

                reason = str(
                    reason
                )

            record = SignalModel(
                timestamp=candle[
                    "timestamp"
                ],
                symbol=candle[
                    "symbol"
                ],
                action=signal.get(
                    "action",
                    "HOLD",
                ),
                price=float(
                    candle["close"]
                ),
                confidence=float(
                    signal.get(
                        "confidence",
                        0.0,
                    )
                ),
                score=int(
                    signal.get(
                        "score",
                        0,
                    )
                ),
                reason=reason,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record.id

        except SQLAlchemyError:

            session.rollback()

            logger.exception(
                "Failed to save signal."
            )

            return None

        finally:

            session.close()

    # ========================================================
    # SAVE TRADE
    # ========================================================

    def save_trade(
        self,
        trade,
    ) -> Optional[int]:
        """
        Save a completed Trade dataclass/object from
        PaperExecutionEngine.trade_history.
        """

        session = SessionLocal()

        try:

            record = TradeModel(
                symbol=trade.symbol,
                side=trade.side,
                quantity=float(
                    trade.quantity
                ),
                entry_price=float(
                    trade.entry_price
                ),
                exit_price=float(
                    trade.exit_price
                ),
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                gross_pnl=float(
                    trade.gross_pnl
                ),
                fees=float(
                    trade.fees
                ),
                net_pnl=float(
                    trade.net_pnl
                ),
                exit_reason=trade.exit_reason,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record.id

        except SQLAlchemyError:

            session.rollback()

            logger.exception(
                "Failed to save trade."
            )

            return None

        finally:

            session.close()

    # ========================================================
    # SAVE ACCOUNT SNAPSHOT
    # ========================================================

    def save_account_snapshot(
        self,
        status: dict,
    ) -> Optional[int]:

        session = SessionLocal()

        try:

            record = AccountSnapshotModel(
                timestamp=datetime.now(
                    timezone.utc
                ),
                cash=float(
                    status.get(
                        "cash",
                        0.0,
                    )
                ),
                equity=float(
                    status.get(
                        "equity",
                        0.0,
                    )
                ),
                realized_pnl=float(
                    status.get(
                        "realized_pnl",
                        0.0,
                    )
                ),
                unrealized_pnl=float(
                    status.get(
                        "unrealized_pnl",
                        0.0,
                    )
                ),
                total_return=float(
                    status.get(
                        "total_return",
                        0.0,
                    )
                ),
                total_trades=int(
                    status.get(
                        "total_trades",
                        0,
                    )
                ),
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record.id

        except SQLAlchemyError:

            session.rollback()

            logger.exception(
                "Failed to save account snapshot."
            )

            return None

        finally:

            session.close()

    # ========================================================
    # SAVE BACKTEST RUN
    # ========================================================

    def save_backtest_run(
        self,
        result: dict,
        timeframe: str,
    ) -> Optional[int]:

        session = SessionLocal()

        try:

            record = BacktestRunModel(
                symbol=result.get(
                    "symbol",
                    "ETHUSDT",
                ),
                timeframe=timeframe,
                candles=int(
                    result.get(
                        "candles",
                        0,
                    )
                ),
                starting_balance=float(
                    result.get(
                        "starting_balance",
                        0.0,
                    )
                ),
                ending_equity=float(
                    result.get(
                        "ending_equity",
                        0.0,
                    )
                ),
                net_profit=float(
                    result.get(
                        "net_profit",
                        0.0,
                    )
                ),
                return_percentage=float(
                    result.get(
                        "return_percentage",
                        0.0,
                    )
                ),
                total_trades=int(
                    result.get(
                        "total_trades",
                        0,
                    )
                ),
                winning_trades=int(
                    result.get(
                        "winning_trades",
                        0,
                    )
                ),
                losing_trades=int(
                    result.get(
                        "losing_trades",
                        0,
                    )
                ),
                win_rate=float(
                    result.get(
                        "win_rate",
                        0.0,
                    )
                ),
                profit_factor=float(
                    result.get(
                        "profit_factor",
                        0.0,
                    )
                ),
                total_fees=float(
                    result.get(
                        "total_fees",
                        0.0,
                    )
                ),
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record.id

        except SQLAlchemyError:

            session.rollback()

            logger.exception(
                "Failed to save backtest run."
            )

            return None

        finally:

            session.close()
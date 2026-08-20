from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from src.database.db import Base


def utc_now():
    return datetime.now(
        timezone.utc
    )


# ============================================================
# CANDLES
# ============================================================

class CandleModel(Base):

    __tablename__ = "candles"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    symbol = Column(
        String(20),
        nullable=False,
        index=True,
    )

    interval = Column(
        String(10),
        nullable=False,
        default="1m",
    )

    open = Column(
        Float,
        nullable=False,
    )

    high = Column(
        Float,
        nullable=False,
    )

    low = Column(
        Float,
        nullable=False,
    )

    close = Column(
        Float,
        nullable=False,
    )

    volume = Column(
        Float,
        nullable=False,
    )

    trade_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# SIGNALS
# ============================================================

class SignalModel(Base):

    __tablename__ = "signals"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    symbol = Column(
        String(20),
        nullable=False,
        index=True,
    )

    action = Column(
        String(10),
        nullable=False,
    )

    price = Column(
        Float,
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    score = Column(
        Integer,
        nullable=False,
        default=0,
    )

    reason = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# TRADES
# ============================================================

class TradeModel(Base):

    __tablename__ = "trades"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    symbol = Column(
        String(20),
        nullable=False,
        index=True,
    )

    side = Column(
        String(10),
        nullable=False,
    )

    quantity = Column(
        Float,
        nullable=False,
    )

    entry_price = Column(
        Float,
        nullable=False,
    )

    exit_price = Column(
        Float,
        nullable=False,
    )

    entry_time = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    exit_time = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    gross_pnl = Column(
        Float,
        nullable=False,
    )

    fees = Column(
        Float,
        nullable=False,
    )

    net_pnl = Column(
        Float,
        nullable=False,
    )

    exit_reason = Column(
        String(50),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# ACCOUNT SNAPSHOTS
# ============================================================

class AccountSnapshotModel(Base):

    __tablename__ = "account_snapshots"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=utc_now,
    )

    cash = Column(
        Float,
        nullable=False,
    )

    equity = Column(
        Float,
        nullable=False,
    )

    realized_pnl = Column(
        Float,
        nullable=False,
    )

    unrealized_pnl = Column(
        Float,
        nullable=False,
    )

    total_return = Column(
        Float,
        nullable=False,
    )

    total_trades = Column(
        Integer,
        nullable=False,
        default=0,
    )


# ============================================================
# BACKTEST RUNS
# ============================================================

class BacktestRunModel(Base):

    __tablename__ = "backtest_runs"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    symbol = Column(
        String(20),
        nullable=False,
        index=True,
    )

    timeframe = Column(
        String(10),
        nullable=False,
    )

    candles = Column(
        Integer,
        nullable=False,
    )

    starting_balance = Column(
        Float,
        nullable=False,
    )

    ending_equity = Column(
        Float,
        nullable=False,
    )

    net_profit = Column(
        Float,
        nullable=False,
    )

    return_percentage = Column(
        Float,
        nullable=False,
    )

    total_trades = Column(
        Integer,
        nullable=False,
    )

    winning_trades = Column(
        Integer,
        nullable=False,
    )

    losing_trades = Column(
        Integer,
        nullable=False,
    )

    win_rate = Column(
        Float,
        nullable=False,
    )

    profit_factor = Column(
        Float,
        nullable=False,
    )

    total_fees = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
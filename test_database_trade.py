from datetime import datetime, timezone

from src.database.repository import TradingRepository
from src.execution.paper import Trade


repository = TradingRepository()


# ============================================================
# TEST TRADE
# ============================================================

trade = Trade(
    symbol="ETHUSDT",
    side="LONG",
    quantity=0.10,

    entry_price=2300.00,

    exit_price=2320.00,

    entry_time=datetime.now(
        timezone.utc
    ),

    exit_time=datetime.now(
        timezone.utc
    ),

    gross_pnl=2.00,

    fees=0.462,

    net_pnl=1.538,

    exit_reason="TAKE_PROFIT",
)


trade_id = repository.save_trade(
    trade
)


print(
    "Trade ID:",
    trade_id,
)


# ============================================================
# TEST ACCOUNT SNAPSHOT
# ============================================================

account_status = {
    "cash": 1001.538,
    "equity": 1001.538,
    "realized_pnl": 1.538,
    "unrealized_pnl": 0.0,
    "total_return": 1.538,
    "total_trades": 1,
}


snapshot_id = (
    repository.save_account_snapshot(
        account_status
    )
)


print(
    "Account Snapshot ID:",
    snapshot_id,
)
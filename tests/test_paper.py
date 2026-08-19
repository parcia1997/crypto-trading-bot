from src.execution.paper import PaperExecutionEngine


def test_buy_and_take_profit():

    engine = PaperExecutionEngine(
        starting_balance=1000.0,
        fee_rate=0.0,
        symbol="ETHUSDT",
    )

    result = engine.open_long(
        quantity=0.1,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    assert result["success"] is True

    assert engine.position is not None

    # Price reaches take profit.
    result = engine.update_price(4040.0)

    assert result["closed"] is True

    assert result["reason"] == "TAKE_PROFIT"

    # 0.1 ETH × $40 = $4 profit
    assert result["net_pnl"] == 4.0

    assert engine.realized_pnl == 4.0

    assert engine.position is None

    assert engine.equity() == 1004.0


def test_stop_loss():

    engine = PaperExecutionEngine(
        starting_balance=1000.0,
        fee_rate=0.0,
    )

    engine.open_long(
        quantity=0.1,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    result = engine.update_price(3980.0)

    assert result["closed"] is True

    assert result["reason"] == "STOP_LOSS"

    # 0.1 ETH × -$20 = -$2
    assert result["net_pnl"] == -2.0

    assert engine.realized_pnl == -2.0


def test_unrealized_pnl():

    engine = PaperExecutionEngine(
        starting_balance=1000.0,
        fee_rate=0.0,
    )

    engine.open_long(
        quantity=0.1,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    engine.update_price(4020.0)

    # 0.1 × $20 = $2
    assert engine.unrealized_pnl() == 2.0

    assert engine.equity() == 1002.0


def test_insufficient_cash():

    engine = PaperExecutionEngine(
        starting_balance=100.0,
        fee_rate=0.0,
    )

    result = engine.open_long(
        quantity=1.0,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    assert result["success"] is False

    assert engine.position is None


def test_cannot_open_two_positions():

    engine = PaperExecutionEngine(
        starting_balance=1000.0,
        fee_rate=0.0,
    )

    first = engine.open_long(
        quantity=0.1,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    assert first["success"] is True

    second = engine.open_long(
        quantity=0.1,
        entry_price=4000.0,
        stop_loss=3980.0,
        take_profit=4040.0,
    )

    assert second["success"] is False
from src.trading_engine import TradingEngine


def test_buy_signal_opens_position():

    engine = TradingEngine(
        starting_balance=1000.0,
        risk_per_trade=0.01,
        fee_rate=0.0,
    )

    signal = {
        "action": "BUY",
        "price": 4000.0,
        "confidence": 0.75,
        "reason": [
            "EMA bullish"
        ],
        "indicators": {
            "atr_14": 20.0
        },
    }

    result = engine.process_signal(
        signal
    )

    assert result["executed"] is True

    assert result["action"] == "BUY"

    assert engine.portfolio.has_position()

    assert (
        engine.portfolio.quantity
        > 0
    )


def test_hold_does_not_trade():

    engine = TradingEngine(
        starting_balance=1000.0
    )

    signal = {
        "action": "HOLD",
        "price": 4000.0,
        "confidence": 0.0,
        "reason": [],
        "indicators": {},
    }

    result = engine.process_signal(
        signal
    )

    assert result["executed"] is False

    assert not engine.portfolio.has_position()


def test_take_profit_closes_position():

    engine = TradingEngine(
        starting_balance=1000.0,
        risk_per_trade=0.01,
        fee_rate=0.0,
    )

    signal = {
        "action": "BUY",
        "price": 4000.0,
        "confidence": 0.75,
        "reason": [],
        "indicators": {
            "atr_14": 20.0
        },
    }

    engine.process_signal(
        signal
    )

    take_profit = 4040.0

    result = engine.update_price(
        take_profit
    )

    assert result["closed"] is True

    assert not engine.portfolio.has_position()

    assert engine.portfolio.realized_pnl > 0


def test_stop_loss_closes_position():

    engine = TradingEngine(
        starting_balance=1000.0,
        risk_per_trade=0.01,
        fee_rate=0.0,
    )

    signal = {
        "action": "BUY",
        "price": 4000.0,
        "confidence": 0.75,
        "reason": [],
        "indicators": {
            "atr_14": 20.0
        },
    }

    engine.process_signal(
        signal
    )

    stop_loss = 3980.0

    result = engine.update_price(
        stop_loss
    )

    assert result["closed"] is True

    assert not engine.portfolio.has_position()

    assert engine.portfolio.realized_pnl < 0
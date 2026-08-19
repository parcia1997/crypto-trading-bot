from src.risk.risk_engine import RiskEngine


def test_buy_risk_calculation():

    engine = RiskEngine(
        account_balance=1000.0,
        risk_per_trade=0.01,
        stop_loss_atr_multiplier=1.0,
        take_profit_atr_multiplier=2.0,
        max_position_percentage=0.25,
    )

    signal = {
        "action": "BUY",
        "price": 4000.0,
        "confidence": 0.75,
        "reason": [
            "EMA bullish",
            "MACD bullish",
        ],
        "indicators": {
            "atr_14": 20.0,
        },
    }

    result = engine.evaluate(signal)

    assert result["approved"] is True

    assert result["action"] == "BUY"

    assert result["entry_price"] == 4000.0

    # $10 maximum risk
    assert result["risk_amount"] == 10.0

    # Stop distance = ATR × 1 = $20
    assert result["stop_loss"] == 3980.0

    # Take profit = ATR × 2 = $40
    assert result["take_profit"] == 4040.0

    # $10 / $20 = 0.5 ETH
    assert result["position_size"] == 0.0625

    assert result["risk_reward"] == 2.0


def test_hold_signal():

    engine = RiskEngine(
        account_balance=1000.0
    )

    signal = {
        "action": "HOLD",
        "price": 4000.0,
        "confidence": 0.0,
        "reason": [
            "No setup"
        ],
        "indicators": {},
    }

    result = engine.evaluate(signal)

    assert result["approved"] is False

    assert result["action"] == "HOLD"

    assert result["position_size"] == 0.0


def test_missing_atr_rejected():

    engine = RiskEngine(
        account_balance=1000.0
    )

    signal = {
        "action": "BUY",
        "price": 4000.0,
        "confidence": 0.75,
        "reason": [],
        "indicators": {},
    }

    result = engine.evaluate(signal)

    assert result["approved"] is False

    assert result["action"] == "REJECTED"
from datetime import datetime, timedelta, timezone

from src.strategy.strategy import TradingStrategy


def create_test_candles(count=100):

    candles = []

    price = 4000.0

    start = datetime.now(timezone.utc)

    for i in range(count):

        price += 2

        candles.append(
            {
                "timestamp": start
                + timedelta(minutes=i),
                "symbol": "ETHUSDT",
                "open": price - 1,
                "high": price + 2,
                "low": price - 2,
                "close": price,
                "volume": 100 + i,
                "trade_count": 100,
            }
        )

    return candles


def test_strategy():

    candles = create_test_candles()

    strategy = TradingStrategy()

    signal = strategy.generate_signal(
        candles
    )

    assert signal["action"] in [
        "BUY",
        "SELL",
        "HOLD",
    ]

    assert "confidence" in signal
    assert "reason" in signal
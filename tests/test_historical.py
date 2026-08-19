import pytest

from src.market.historical import BinanceHistoricalData


@pytest.mark.asyncio
async def test_fetch_historical_candles():

    loader = BinanceHistoricalData(
        symbol="ETHUSDT",
        interval="1m",
        limit=500,
    )

    candles = await loader.fetch()

    assert len(candles) == 500

    first = candles[0]

    required_fields = [
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trade_count",
    ]

    for field in required_fields:
        assert field in first

    assert first["symbol"] == "ETHUSDT"

    assert first["open"] > 0
    assert first["high"] > 0
    assert first["low"] > 0
    assert first["close"] > 0
    assert first["volume"] >= 0
from datetime import datetime, timezone

from src.database.repository import TradingRepository


repository = TradingRepository()


candle = {
    "timestamp": datetime.now(
        timezone.utc
    ),
    "symbol": "ETHUSDT",
    "open": 2300.00,
    "high": 2310.00,
    "low": 2295.00,
    "close": 2305.00,
    "volume": 100.50,
    "trade_count": 500,
}


candle_id = repository.save_candle(
    candle,
    interval="1m",
)


print(
    "Candle ID:",
    candle_id,
)


signal = {
    "action": "BUY",
    "confidence": 0.75,
    "score": 3,
    "reason": [
        "EMA bullish",
        "RSI bullish",
        "MACD bullish",
    ],
}


signal_id = repository.save_signal(
    signal,
    candle,
)


print(
    "Signal ID:",
    signal_id,
)
import logging
from datetime import datetime, timezone
from typing import Callable, Optional


logger = logging.getLogger(__name__)


class CandleBuilder:
    """
    Builds OHLCV candles from real-time trade data.

    Example:

        Trades
           │
           ▼
        CandleBuilder
           │
           ▼
        1-minute candle

    Candle:

        open
        high
        low
        close
        volume
    """

    def __init__(
        self,
        interval_seconds: int = 60,
        on_candle: Optional[Callable] = None,
    ):
        self.interval_seconds = interval_seconds
        self.on_candle = on_candle

        self.current_candle = None

    def process_trade(self, trade: dict):
        """
        Process one trade.

        The trade should contain:

            price
            quantity
            trade_time
            symbol
        """

        price = float(trade["price"])
        quantity = float(trade["quantity"])

        timestamp_ms = int(trade["trade_time"])

        timestamp = datetime.fromtimestamp(
            timestamp_ms / 1000,
            tz=timezone.utc,
        )

        candle_start = self._get_candle_start(timestamp)

        # No candle exists yet.
        if self.current_candle is None:

            self.current_candle = self._create_candle(
                trade,
                candle_start,
            )

            return

        current_start = self.current_candle["timestamp"]

        # Same candle interval.
        if candle_start == current_start:

            self._update_candle(
                price,
                quantity,
            )

            return

        # New candle interval.
        if candle_start > current_start:

            completed_candle = self.current_candle.copy()

            self._emit_candle(
                completed_candle
            )

            self.current_candle = self._create_candle(
                trade,
                candle_start,
            )

            return

        # Older/out-of-order trade.
        logger.warning(
            "Ignoring out-of-order trade: %s",
            trade,
        )

    def _create_candle(
        self,
        trade: dict,
        candle_start: datetime,
    ) -> dict:
        """
        Create a new candle.
        """

        price = float(trade["price"])
        quantity = float(trade["quantity"])

        return {
            "timestamp": candle_start,
            "symbol": trade["symbol"],
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": quantity,
            "trade_count": 1,
        }

    def _update_candle(
        self,
        price: float,
        quantity: float,
    ):
        """
        Update the currently active candle.
        """

        self.current_candle["high"] = max(
            self.current_candle["high"],
            price,
        )

        self.current_candle["low"] = min(
            self.current_candle["low"],
            price,
        )

        self.current_candle["close"] = price

        self.current_candle["volume"] += quantity

        self.current_candle["trade_count"] += 1

    def _emit_candle(
        self,
        candle: dict,
    ):
        """
        Send completed candle to the next component.
        """

        logger.info(
            "CANDLE CLOSED | %s | "
            "O=%.2f H=%.2f L=%.2f C=%.2f V=%.6f",
            candle["symbol"],
            candle["open"],
            candle["high"],
            candle["low"],
            candle["close"],
            candle["volume"],
        )

        if self.on_candle is not None:

            self.on_candle(candle)

    def _get_candle_start(
        self,
        timestamp: datetime,
    ) -> datetime:
        """
        Calculate the beginning of the candle interval.

        For a 60-second interval:

            12:01:15 -> 12:01:00
            12:01:42 -> 12:01:00
            12:02:03 -> 12:02:00
        """

        timestamp_seconds = int(
            timestamp.timestamp()
        )

        candle_start_seconds = (
            timestamp_seconds
            // self.interval_seconds
        ) * self.interval_seconds

        return datetime.fromtimestamp(
            candle_start_seconds,
            tz=timezone.utc,
        )

    def flush(self):
        """
        Return the current candle.

        Useful when shutting down the application.
        """

        if self.current_candle is None:
            return None

        candle = self.current_candle.copy()

        self.current_candle = None

        return candle
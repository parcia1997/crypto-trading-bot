import logging
from typing import List, Dict, Optional


logger = logging.getLogger(__name__)


class CandleStore:
    """
    In-memory rolling candle store.

    Keeps the most recent candles and prevents
    duplicate timestamps.
    """

    def __init__(self, max_candles: int = 2000):
        self.max_candles = max_candles
        self._candles: Dict = {}

    def load(self, candles: List[dict]):
        """
        Load historical candles.
        """

        for candle in candles:
            self.add(candle)

        logger.info(
            "Loaded %s candles into CandleStore.",
            len(self._candles),
        )

    def add(self, candle: dict) -> bool:
        """
        Add a candle.

        Returns:
            True  -> candle was added/updated
            False -> invalid candle
        """

        timestamp = candle.get("timestamp")

        if timestamp is None:
            logger.warning(
                "Ignoring candle without timestamp."
            )
            return False

        self._candles[timestamp] = candle

        self._trim()

        return True

    def get_all(self) -> List[dict]:
        """
        Return candles ordered by timestamp.
        """

        return sorted(
            self._candles.values(),
            key=lambda candle: candle["timestamp"],
        )

    def get_latest(
        self,
        count: int = 1,
    ) -> List[dict]:
        """
        Return the latest N candles.
        """

        candles = self.get_all()

        if count <= 0:
            return []

        return candles[-count:]

    def latest(self) -> Optional[dict]:
        """
        Return the most recent candle.
        """

        candles = self.get_latest(1)

        if not candles:
            return None

        return candles[0]

    def count(self) -> int:
        """
        Return number of candles stored.
        """

        return len(self._candles)

    def _trim(self):
        """
        Keep only max_candles.
        """

        if len(self._candles) <= self.max_candles:
            return

        timestamps = sorted(
            self._candles.keys()
        )

        excess = (
            len(timestamps)
            - self.max_candles
        )

        for timestamp in timestamps[:excess]:
            del self._candles[timestamp]
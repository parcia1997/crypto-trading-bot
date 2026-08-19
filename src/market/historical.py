import logging
from typing import List, Dict

import aiohttp


logger = logging.getLogger(__name__)


class BinanceHistoricalData:
    """
    Downloads historical OHLCV candles from Binance.

    Default:
        ETHUSDT
        1-minute candles
        500 candles
    """

    BASE_URL = "https://api.binance.com/api/v3/klines"

    def __init__(
        self,
        symbol: str = "ETHUSDT",
        interval: str = "1m",
        limit: int = 500,
    ):
        self.symbol = symbol.upper()
        self.interval = interval
        self.limit = limit

    async def fetch(self) -> List[Dict]:
        """
        Fetch historical candles from Binance.
        """

        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": self.limit,
        }

        logger.info(
            "Fetching %s historical candles for %s...",
            self.limit,
            self.symbol,
        )

        timeout = aiohttp.ClientTimeout(
            total=30
        )

        try:

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                async with session.get(
                    self.BASE_URL,
                    params=params,
                ) as response:

                    if response.status != 200:

                        error_text = await response.text()

                        raise RuntimeError(
                            f"Binance API returned "
                            f"{response.status}: "
                            f"{error_text}"
                        )

                    data = await response.json()

            candles = self._parse_candles(data)

            logger.info(
                "Successfully loaded %s candles.",
                len(candles),
            )

            return candles

        except aiohttp.ClientError as exc:

            logger.exception(
                "Network error while fetching "
                "historical data: %s",
                exc,
            )

            raise

    def _parse_candles(
        self,
        data: list,
    ) -> List[Dict]:

        candles = []

        for item in data:

            if len(item) < 6:
                continue

            candle = {
                "timestamp": self._timestamp(
                    item[0]
                ),
                "symbol": self.symbol,
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "trade_count": int(item[8])
                if len(item) > 8
                else 0,
            }

            candles.append(candle)

        return candles

    @staticmethod
    def _timestamp(timestamp_ms: int):

        from datetime import datetime, timezone

        return datetime.fromtimestamp(
            int(timestamp_ms) / 1000,
            tz=timezone.utc,
        )
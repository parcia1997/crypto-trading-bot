import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp


logger = logging.getLogger(__name__)


class BinanceHistoricalData:
    """
    Downloads historical OHLCV candles from Binance.

    Supports pagination so we can request more than
    one API batch.

    Example:
        ETHUSDT
        1-minute candles
        10,000 candles
    """

    BASE_URL = "https://api.binance.com/api/v3/klines"

    # Binance kline endpoint supports a maximum
    # batch size of 1000 candles per request.
    MAX_BATCH_SIZE = 1000

    def __init__(
        self,
        symbol: str = "ETHUSDT",
        interval: str = "1m",
        limit: int = 500,
        request_delay: float = 0.10,
    ):
        if limit <= 0:
            raise ValueError(
                "limit must be greater than 0."
            )

        if request_delay < 0:
            raise ValueError(
                "request_delay cannot be negative."
            )

        self.symbol = symbol.upper()
        self.interval = interval

        # Total candles requested.
        self.limit = limit

        # Small delay between paginated requests.
        self.request_delay = request_delay

    # ========================================================
    # FETCH
    # ========================================================

    async def fetch(
        self,
    ) -> List[Dict]:
        """
        Fetch historical candles.

        If limit <= 1000:
            one Binance request

        If limit > 1000:
            multiple paginated requests

        Candles are returned oldest -> newest.
        """

        logger.info(
            "Fetching %s historical candles "
            "for %s | interval=%s",
            self.limit,
            self.symbol,
            self.interval,
        )

        timeout = aiohttp.ClientTimeout(
            total=60
        )

        candles: List[Dict] = []

        # endTime tells Binance:
        # "give me candles before this timestamp".
        end_time: Optional[int] = None

        remaining = self.limit

        try:

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                while remaining > 0:

                    batch_size = min(
                        remaining,
                        self.MAX_BATCH_SIZE,
                    )

                    data = await self._fetch_batch(
                        session=session,
                        limit=batch_size,
                        end_time=end_time,
                    )

                    if not data:

                        logger.warning(
                            "Binance returned no more candles."
                        )

                        break

                    batch = self._parse_candles(
                        data
                    )

                    if not batch:

                        logger.warning(
                            "No valid candles in Binance response."
                        )

                        break

                    # We are fetching backwards.
                    #
                    # New batch is older than the candles
                    # already collected, so prepend it.
                    candles = (
                        batch
                        + candles
                    )

                    logger.info(
                        "Historical batch loaded | "
                        "batch=%s | "
                        "collected=%s/%s",
                        len(batch),
                        len(candles),
                        self.limit,
                    )

                    remaining = (
                        self.limit
                        - len(candles)
                    )

                    if remaining <= 0:
                        break

                    # ----------------------------------------
                    # MOVE BACKWARD IN TIME
                    # ----------------------------------------

                    oldest_open_time_ms = int(
                        data[0][0]
                    )

                    # Request candles strictly before
                    # the oldest candle we already have.
                    end_time = (
                        oldest_open_time_ms
                        - 1
                    )

                    # Avoid hammering Binance.
                    if self.request_delay > 0:

                        await asyncio.sleep(
                            self.request_delay
                        )

        except aiohttp.ClientError as exc:

            logger.exception(
                "Network error while fetching "
                "historical data: %s",
                exc,
            )

            raise

        # ====================================================
        # REMOVE DUPLICATES
        # ====================================================

        candles = self._deduplicate(
            candles
        )

        # If for any reason pagination returned slightly
        # more than requested, keep only the latest N.
        candles = candles[
            -self.limit:
        ]

        logger.info(
            "Successfully loaded %s historical candles.",
            len(candles),
        )

        return candles

    # ========================================================
    # FETCH ONE BATCH
    # ========================================================

    async def _fetch_batch(
        self,
        session: aiohttp.ClientSession,
        limit: int,
        end_time: Optional[int] = None,
    ) -> list:
        """
        Fetch one Binance kline batch.
        """

        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": limit,
        }

        if end_time is not None:

            params["endTime"] = (
                end_time
            )

        async with session.get(
            self.BASE_URL,
            params=params,
        ) as response:

            if response.status != 200:

                error_text = (
                    await response.text()
                )

                raise RuntimeError(
                    f"Binance API returned "
                    f"{response.status}: "
                    f"{error_text}"
                )

            return await response.json()

    # ========================================================
    # PARSE CANDLES
    # ========================================================

    def _parse_candles(
        self,
        data: list,
    ) -> List[Dict]:

        candles = []

        for item in data:

            if len(item) < 6:
                continue

            candle = {
                "timestamp":
                    self._timestamp(
                        item[0]
                    ),

                "symbol":
                    self.symbol,

                "open":
                    float(item[1]),

                "high":
                    float(item[2]),

                "low":
                    float(item[3]),

                "close":
                    float(item[4]),

                "volume":
                    float(item[5]),

                "trade_count":
                    int(item[8])
                    if len(item) > 8
                    else 0,
            }

            candles.append(
                candle
            )

        return candles

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    @staticmethod
    def _deduplicate(
        candles: List[Dict],
    ) -> List[Dict]:
        """
        Remove duplicate timestamps and
        return candles sorted oldest -> newest.
        """

        candle_map = {}

        for candle in candles:

            timestamp = candle.get(
                "timestamp"
            )

            if timestamp is None:
                continue

            candle_map[
                timestamp
            ] = candle

        return sorted(
            candle_map.values(),
            key=lambda candle:
                candle["timestamp"],
        )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    @staticmethod
    def _timestamp(
        timestamp_ms: int,
    ) -> datetime:

        return datetime.fromtimestamp(
            int(timestamp_ms) / 1000,
            tz=timezone.utc,
        )
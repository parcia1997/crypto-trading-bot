import asyncio
import json
import logging
from typing import Callable, Optional

import websockets


logger = logging.getLogger(__name__)


class BinanceWebSocket:
    """
    Real-time Binance WebSocket client.

    Receives ETH/USDT trade data and forwards each trade
    to a callback function.
    """

    BASE_URL = "wss://stream.binance.com:9443/ws"

    def __init__(
        self,
        symbol: str = "ethusdt",
        on_trade: Optional[Callable] = None,
        reconnect_delay: int = 5,
    ):
        self.symbol = symbol.lower()
        self.on_trade = on_trade
        self.reconnect_delay = reconnect_delay

        self.running = False
        self.websocket = None

    @property
    def stream_url(self) -> str:
        """
        Binance trade stream URL.
        """
        return f"{self.BASE_URL}/{self.symbol}@trade"

    async def connect(self):
        """
        Connect to Binance WebSocket and continuously
        receive trade data.
        """

        self.running = True

        while self.running:

            try:
                logger.info(
                    "Connecting to Binance WebSocket: %s",
                    self.stream_url,
                )

                async with websockets.connect(
                    self.stream_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                ) as websocket:

                    self.websocket = websocket

                    logger.info(
                        "Connected to Binance WebSocket"
                    )

                    await self._receive_messages()

            except asyncio.CancelledError:
                logger.info(
                    "WebSocket task cancelled."
                )
                break

            except Exception as exc:
                logger.exception(
                    "WebSocket connection error: %s",
                    exc,
                )

                if self.running:
                    logger.info(
                        "Reconnecting in %s seconds...",
                        self.reconnect_delay,
                    )

                    await asyncio.sleep(
                        self.reconnect_delay
                    )

            finally:
                self.websocket = None

    async def _receive_messages(self):
        """
        Receive messages from Binance.
        """

        if self.websocket is None:
            return

        async for message in self.websocket:

            try:
                data = json.loads(message)

                trade = self._parse_trade(data)

                if trade is None:
                    continue

                if self.on_trade is not None:

                    result = self.on_trade(trade)

                    if asyncio.iscoroutine(result):
                        await result

            except json.JSONDecodeError:
                logger.warning(
                    "Received invalid JSON message."
                )

            except Exception as exc:
                logger.exception(
                    "Error processing WebSocket message: %s",
                    exc,
                )

    @staticmethod
    def _parse_trade(data: dict) -> Optional[dict]:
        """
        Convert Binance trade message into our internal
        trade representation.

        Binance trade message contains fields such as:

        e = event type
        E = event time
        s = symbol
        t = trade ID
        p = price
        q = quantity
        T = trade timestamp
        m = buyer is market maker
        """

        if data.get("e") != "trade":
            return None

        try:
            return {
                "event_type": data["e"],
                "event_time": data["E"],
                "symbol": data["s"],
                "trade_id": data["t"],
                "price": float(data["p"]),
                "quantity": float(data["q"]),
                "trade_time": data["T"],
                "is_buyer_maker": data["m"],
            }

        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Invalid trade message: %s",
                exc,
            )

            return None

    async def stop(self):
        """
        Stop the WebSocket client.
        """

        logger.info(
            "Stopping Binance WebSocket..."
        )

        self.running = False

        if self.websocket is not None:

            try:
                await self.websocket.close()

            except Exception as exc:
                logger.warning(
                    "Error closing WebSocket: %s",
                    exc,
                )

        self.websocket = None
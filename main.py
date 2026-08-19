import asyncio
import logging

from src.market.websocket import BinanceWebSocket
from src.market.candle_builder import CandleBuilder


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def on_candle(candle):
    print()
    print("=" * 60)
    print("NEW ETH/USDT CANDLE")
    print("=" * 60)

    print(f"Time:         {candle['timestamp']}")
    print(f"Open:         {candle['open']}")
    print(f"High:         {candle['high']}")
    print(f"Low:          {candle['low']}")
    print(f"Close:        {candle['close']}")
    print(f"Volume:       {candle['volume']}")
    print(f"Trades:       {candle['trade_count']}")

    print("=" * 60)


async def main():

    candle_builder = CandleBuilder(
        interval_seconds=60,
        on_candle=on_candle,
    )

    websocket_client = BinanceWebSocket(
        symbol="ethusdt",
        on_trade=candle_builder.process_trade,
    )

    try:

        await websocket_client.connect()

    except KeyboardInterrupt:

        print("Stopping bot...")

    finally:

        await websocket_client.stop()

        final_candle = candle_builder.flush()

        if final_candle:
            print(
                "Final incomplete candle:",
                final_candle,
            )


if __name__ == "__main__":
    asyncio.run(main())
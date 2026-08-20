import asyncio
import logging

from src.market.historical import BinanceHistoricalData
from src.backtest.backtester import Backtester


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main():

    logger.info(
        "Starting ETHUSDT backtest..."
    )

    historical = BinanceHistoricalData(
        symbol="ETHUSDT",
        interval="1m",
        limit=1000,
    )

    candles = await historical.fetch()

    logger.info(
        "Loaded %s candles for backtest.",
        len(candles),
    )

    backtester = Backtester(
        symbol="ETHUSDT",
        starting_balance=1000.0,
        warmup_candles=50,
    )

    result = backtester.run(
        candles
    )

    print()
    print("=" * 55)
    print("ETHUSDT BACKTEST RESULTS")
    print("=" * 55)

    print(
        f"Starting Balance : "
        f"${result['starting_balance']:.2f}"
    )

    print(
        f"Ending Equity    : "
        f"${result['ending_equity']:.2f}"
    )

    print(
        f"Net Profit       : "
        f"${result['net_profit']:.2f}"
    )

    print(
        f"Return           : "
        f"{result['return_percentage']:.2f}%"
    )

    print(
        f"Total Trades     : "
        f"{result['total_trades']}"
    )

    print(
        f"Winning Trades   : "
        f"{result['winning_trades']}"
    )

    print(
        f"Losing Trades    : "
        f"{result['losing_trades']}"
    )

    print(
        f"Win Rate         : "
        f"{result['win_rate']:.2f}%"
    )

    print(
        f"Profit Factor    : "
        f"{result['profit_factor']:.2f}"
    )

    print(
        f"Average Win      : "
        f"${result['average_win']:.4f}"
    )

    print(
        f"Average Loss     : "
        f"${result['average_loss']:.4f}"
    )

    print(
        f"Total Fees       : "
        f"${result['total_fees']:.4f}"
    )

    print(
        f"BUY Signals      : "
        f"{result['signals_buy']}"
    )

    print(
        f"SELL Signals     : "
        f"{result['signals_sell']}"
    )

    print(
        f"HOLD Signals     : "
        f"{result['signals_hold']}"
    )

    print(
        f"Rejected Trades  : "
        f"{result['rejected_trades']}"
    )

    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
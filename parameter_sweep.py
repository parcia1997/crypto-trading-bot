import asyncio
import logging

from src.market.historical import BinanceHistoricalData
from src.backtest.backtester import Backtester
from src.bot.trading_bot import TradingBot


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


THRESHOLDS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
]


async def main():

    print()
    print("=" * 90)
    print("ETHUSDT MINIMUM NET RETURN PARAMETER SWEEP")
    print("=" * 90)

    historical = BinanceHistoricalData(
        symbol="ETHUSDT",
        interval="1m",
        limit=10000,
    )

    candles = await historical.fetch()

    print(
        f"Historical candles loaded: {len(candles)}"
    )

    print()

    results = []

    for threshold in THRESHOLDS:

        backtester = Backtester(
            symbol="ETHUSDT",
            starting_balance=1000.0,
            warmup_candles=50,
        )

        # Replace the default bot with one
        # configured for this threshold.
        backtester.bot = TradingBot(
            symbol="ETHUSDT",
            starting_balance=1000.0,
            minimum_expected_net_return_percentage=(
                threshold
            ),
            enable_database=False,
        )

        result = backtester.run(
            candles
        )

        result["threshold"] = threshold

        results.append(
            result
        )

    print(
        f"{'Threshold':<12}"
        f"{'Trades':<10}"
        f"{'Wins':<8}"
        f"{'Losses':<8}"
        f"{'Win Rate':<12}"
        f"{'Net P&L':<12}"
        f"{'Return':<10}"
        f"{'Fees':<10}"
        f"{'PF':<10}"
        f"{'Rejected':<10}"
    )

    print("-" * 100)

    for result in results:

        print(
            f"{result['threshold']:<12.2f}"
            f"{result['total_trades']:<10}"
            f"{result['winning_trades']:<8}"
            f"{result['losing_trades']:<8}"
            f"{result['win_rate']:<12.2f}"
            f"${result['net_profit']:<11.2f}"
            f"{result['return_percentage']:<10.2f}"
            f"${result['total_fees']:<9.2f}"
            f"{result['profit_factor']:<10.2f}"
            f"{result['rejected_trades']:<10}"
        )

    print()
    print("=" * 90)

    best_result = max(
        results,
        key=lambda item: item[
            "net_profit"
        ],
    )

    print(
        "BEST RESULT BY NET PROFIT"
    )

    print("-" * 90)

    print(
        f"Threshold      : "
        f"{best_result['threshold']:.2f}%"
    )

    print(
        f"Total Trades   : "
        f"{best_result['total_trades']}"
    )

    print(
        f"Win Rate       : "
        f"{best_result['win_rate']:.2f}%"
    )

    print(
        f"Net Profit     : "
        f"${best_result['net_profit']:.2f}"
    )

    print(
        f"Return         : "
        f"{best_result['return_percentage']:.2f}%"
    )

    print(
        f"Profit Factor  : "
        f"{best_result['profit_factor']:.2f}"
    )

    print(
        f"Total Fees     : "
        f"${best_result['total_fees']:.2f}"
    )

    print(
        f"Rejected       : "
        f"{best_result['rejected_trades']}"
    )

    print("=" * 90)


if __name__ == "__main__":

    asyncio.run(
        main()
    )
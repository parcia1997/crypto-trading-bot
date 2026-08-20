import asyncio
import logging

from src.market.historical import BinanceHistoricalData
from src.backtest.backtester import Backtester
from src.bot.trading_bot import TradingBot


# Reduce logging during the experiment
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


SYMBOL = "ETHUSDT"
STARTING_BALANCE = 1000.0

# Test multiple candle timeframes
TIMEFRAMES = [
    "1m",
    "5m",
    "15m",
]

# Test multiple fee-aware minimum returns
THRESHOLDS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
]

# Number of candles for each timeframe
CANDLE_LIMIT = 10000


async def main():

    print()
    print("=" * 110)
    print("ETHUSDT TIMEFRAME + NET RETURN PARAMETER SWEEP")
    print("=" * 110)

    results = []

    # ========================================================
    # TEST EACH TIMEFRAME
    # ========================================================

    for timeframe in TIMEFRAMES:

        print()
        print(
            f"Loading {CANDLE_LIMIT} candles "
            f"for timeframe {timeframe}..."
        )

        historical = BinanceHistoricalData(
            symbol=SYMBOL,
            interval=timeframe,
            limit=CANDLE_LIMIT,
        )

        candles = await historical.fetch()

        print(
            f"Loaded {len(candles)} "
            f"{timeframe} candles."
        )

        # ====================================================
        # TEST EACH THRESHOLD
        # ====================================================

        for threshold in THRESHOLDS:

            print(
                f"Testing {timeframe} | "
                f"threshold={threshold:.2f}%"
            )

            backtester = Backtester(
                symbol=SYMBOL,
                starting_balance=STARTING_BALANCE,
                warmup_candles=50,
            )

            # Replace default bot with one configured
            # for this particular experiment.
            backtester.bot = TradingBot(
                symbol=SYMBOL,
                starting_balance=STARTING_BALANCE,
                minimum_expected_net_return_percentage=(
                    threshold
                ),
                enable_database=False,
            )

            result = backtester.run(
                candles
            )

            result["timeframe"] = (
                timeframe
            )

            result["threshold"] = (
                threshold
            )

            results.append(
                result
            )

    # ========================================================
    # PRINT COMPARISON
    # ========================================================

    print()
    print("=" * 110)
    print("TIMEFRAME COMPARISON")
    print("=" * 110)

    print(
        f"{'TF':<7}"
        f"{'Threshold':<12}"
        f"{'Trades':<9}"
        f"{'Wins':<7}"
        f"{'Loss':<7}"
        f"{'Win Rate':<12}"
        f"{'Net P&L':<13}"
        f"{'Return':<11}"
        f"{'Fees':<11}"
        f"{'PF':<9}"
        f"{'Rejected':<10}"
    )

    print("-" * 110)

    for result in results:

        print(
            f"{result['timeframe']:<7}"
            f"{result['threshold']:<12.2f}"
            f"{result['total_trades']:<9}"
            f"{result['winning_trades']:<7}"
            f"{result['losing_trades']:<7}"
            f"{result['win_rate']:<12.2f}"
            f"${result['net_profit']:<12.2f}"
            f"{result['return_percentage']:<11.2f}"
            f"${result['total_fees']:<10.2f}"
            f"{result['profit_factor']:<9.2f}"
            f"{result['rejected_trades']:<10}"
        )

    # ========================================================
    # BEST RESULT
    # ========================================================

    best_result = max(
        results,
        key=lambda item: item[
            "net_profit"
        ],
    )

    print()
    print("=" * 110)
    print("BEST RESULT BY NET PROFIT")
    print("-" * 110)

    print(
        f"Timeframe      : "
        f"{best_result['timeframe']}"
    )

    print(
        f"Threshold      : "
        f"{best_result['threshold']:.2f}%"
    )

    print(
        f"Total Trades   : "
        f"{best_result['total_trades']}"
    )

    print(
        f"Winning Trades : "
        f"{best_result['winning_trades']}"
    )

    print(
        f"Losing Trades  : "
        f"{best_result['losing_trades']}"
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

    print("=" * 110)


if __name__ == "__main__":

    asyncio.run(
        main()
    )
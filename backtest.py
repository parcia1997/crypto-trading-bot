import asyncio
import logging

from src.market.historical import BinanceHistoricalData
from src.backtest.backtester import Backtester


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# MAIN
# ============================================================

async def main():

    logger.info(
        "Starting ETHUSDT backtest..."
    )

    # --------------------------------------------------------
    # HISTORICAL DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # BACKTESTER
    # --------------------------------------------------------

    backtester = Backtester(
        symbol="ETHUSDT",
        starting_balance=1000.0,
        warmup_candles=50,
    )

    result = backtester.run(
        candles
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 60)

    print(
        "ETHUSDT BACKTEST RESULTS"
    )

    print("=" * 60)

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

    print()

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

    print()

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

    print()

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

    # ========================================================
    # REJECTION ANALYSIS
    # ========================================================

    print()

    print(
        "REJECTION ANALYSIS"
    )

    print("-" * 60)

    rejections = result.get(
        "rejection_reasons",
        {},
    )

    if not rejections:

        print(
            "No rejected trade reasons recorded."
        )

    else:

        sorted_rejections = sorted(
            rejections.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for reason, count in sorted_rejections:

            print(
                f"{reason:<35} : {count}"
            )

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
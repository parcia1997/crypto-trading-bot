import asyncio
import logging

from src.market.historical import BinanceHistoricalData
from src.backtest.backtester import Backtester
from src.bot.trading_bot import TradingBot


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "ETHUSDT"

TIMEFRAME = "1m"

STARTING_BALANCE = 1000.0

CANDLE_LIMIT = 10000

MINIMUM_NET_RETURN = 0.15


# ============================================================
# ATR COMBINATIONS
# ============================================================

ATR_COMBINATIONS = [
    (1.00, 2.00),
    (1.00, 2.50),
    (1.00, 3.00),
    (1.25, 2.50),
    (1.25, 3.00),
    (1.50, 3.00),
    (1.50, 4.00),
]


# Disable detailed logs during sweep.
logging.disable(
    logging.CRITICAL
)


# ============================================================
# MAIN
# ============================================================

async def main():

    print()

    print("=" * 115)

    print(
        "ETHUSDT ATR STOP-LOSS / TAKE-PROFIT SWEEP"
    )

    print("=" * 115)

    print(
        f"Timeframe          : {TIMEFRAME}"
    )

    print(
        f"Candles            : {CANDLE_LIMIT}"
    )

    print(
        f"Starting Balance   : ${STARTING_BALANCE:.2f}"
    )

    print(
        f"Minimum Net Return : {MINIMUM_NET_RETURN:.2f}%"
    )

    print()

    # ========================================================
    # DOWNLOAD DATA ONCE
    # ========================================================

    historical = BinanceHistoricalData(
        symbol=SYMBOL,
        interval=TIMEFRAME,
        limit=CANDLE_LIMIT,
    )

    candles = await historical.fetch()

    print(
        f"Historical candles loaded: "
        f"{len(candles)}"
    )

    print()

    results = []

    # ========================================================
    # RUN EACH ATR COMBINATION
    # ========================================================

    for (
        stop_loss_multiplier,
        take_profit_multiplier,
    ) in ATR_COMBINATIONS:

        print(
            f"Testing SL={stop_loss_multiplier:.2f} ATR | "
            f"TP={take_profit_multiplier:.2f} ATR..."
        )

        # ----------------------------------------------------
        # BACKTESTER
        # ----------------------------------------------------

        backtester = Backtester(
            symbol=SYMBOL,
            starting_balance=STARTING_BALANCE,
            warmup_candles=50,
        )

        # ----------------------------------------------------
        # CUSTOM BOT
        # ----------------------------------------------------

        backtester.bot = TradingBot(
            symbol=SYMBOL,
            starting_balance=STARTING_BALANCE,
            enable_database=False,

            stop_loss_atr_multiplier=(
                stop_loss_multiplier
            ),

            take_profit_atr_multiplier=(
                take_profit_multiplier
            ),

            minimum_expected_net_return_percentage=(
                MINIMUM_NET_RETURN
            ),
        )

        # ----------------------------------------------------
        # RUN BACKTEST
        # ----------------------------------------------------

        result = backtester.run(
            candles
        )

        result[
            "stop_loss_atr"
        ] = stop_loss_multiplier

        result[
            "take_profit_atr"
        ] = take_profit_multiplier

        results.append(
            result
        )

    # ========================================================
    # RESULTS TABLE
    # ========================================================

    print()
    print("=" * 115)

    print(
        "ATR PARAMETER COMPARISON"
    )

    print("=" * 115)

    print(
        f"{'SL ATR':<10}"
        f"{'TP ATR':<10}"
        f"{'Trades':<10}"
        f"{'Wins':<8}"
        f"{'Losses':<9}"
        f"{'Win Rate':<12}"
        f"{'Net P&L':<13}"
        f"{'Return':<11}"
        f"{'Fees':<11}"
        f"{'PF':<10}"
        f"{'Rejected':<10}"
    )

    print("-" * 115)

    for result in results:

        print(
            f"{result['stop_loss_atr']:<10.2f}"
            f"{result['take_profit_atr']:<10.2f}"
            f"{result['total_trades']:<10}"
            f"{result['winning_trades']:<8}"
            f"{result['losing_trades']:<9}"
            f"{result['win_rate']:<12.2f}"
            f"${result['net_profit']:<12.2f}"
            f"{result['return_percentage']:<11.2f}"
            f"${result['total_fees']:<10.2f}"
            f"{result['profit_factor']:<10.2f}"
            f"{result['rejected_trades']:<10}"
        )

    # ========================================================
    # BEST NET PROFIT
    # ========================================================

    best_result = max(
        results,
        key=lambda item:
            item["net_profit"],
    )

    print()
    print("=" * 115)

    print(
        "BEST ATR CONFIGURATION BY NET PROFIT"
    )

    print("-" * 115)

    print(
        f"Stop Loss ATR  : "
        f"{best_result['stop_loss_atr']:.2f}"
    )

    print(
        f"Take Profit ATR: "
        f"{best_result['take_profit_atr']:.2f}"
    )

    print(
        f"Trades         : "
        f"{best_result['total_trades']}"
    )

    print(
        f"Wins           : "
        f"{best_result['winning_trades']}"
    )

    print(
        f"Losses         : "
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

    print("=" * 115)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
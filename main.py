import asyncio
import logging

from src.bot.trading_bot import TradingBot

from src.market.websocket import BinanceWebSocket
from src.market.candle_builder import CandleBuilder
from src.market.historical import BinanceHistoricalData


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "ETHUSDT"

STARTING_BALANCE = 1000.0

HISTORICAL_CANDLES = 500


# ============================================================
# BOT
# ============================================================

bot = TradingBot(
    symbol=SYMBOL,
    starting_balance=STARTING_BALANCE,
)


# ============================================================
# CANDLE CALLBACK
# ============================================================

def on_candle(candle: dict):
    """
    Called whenever a 1-minute candle closes.

    CandleBuilder
        ↓
    TradingBot
    """

    logger.info(
        "NEW CANDLE | %s | "
        "O=%.2f H=%.2f L=%.2f C=%.2f V=%.6f",
        candle["symbol"],
        candle["open"],
        candle["high"],
        candle["low"],
        candle["close"],
        candle["volume"],
    )

    result = bot.process_candle(
        candle
    )

    logger.info(
        "BOT RESULT | action=%s | executed=%s",
        result.get("action"),
        result.get("executed"),
    )

    logger.info(
        "BOT SUMMARY | %s",
        bot.summary(),
    )


# ============================================================
# CANDLE BUILDER
# ============================================================

candle_builder = CandleBuilder(
    interval_seconds=60,
    on_candle=on_candle,
)


# ============================================================
# TRADE CALLBACK
# ============================================================

async def on_trade(trade: dict):
    """
    Called for every Binance trade.

    Binance WebSocket
        ↓
    CandleBuilder
    """

    candle_builder.process_trade(
        trade
    )


# ============================================================
# HISTORICAL DATA
# ============================================================

async def load_historical_data():

    logger.info(
        "Loading %s historical candles...",
        HISTORICAL_CANDLES,
    )

    historical = BinanceHistoricalData(
        symbol=SYMBOL,
        interval="1m",
        limit=HISTORICAL_CANDLES,
    )

    candles = await historical.fetch()

    # Load historical candles directly
    # into TradingBot's CandleStore.

    bot.candle_store.load(
        candles
    )

    logger.info(
        "Historical data loaded: %s candles",
        bot.candle_store.count(),
    )


# ============================================================
# STATUS LOOP
# ============================================================

async def status_loop():

    while True:

        await asyncio.sleep(30)

        status = bot.status()

        account = status["account"]

        logger.info(
            "ACCOUNT | "
            "cash=%.2f | "
            "equity=%.2f | "
            "realized_pnl=%.4f | "
            "unrealized_pnl=%.4f | "
            "trades=%s",
            account["cash"],
            account["equity"],
            account["realized_pnl"],
            account["unrealized_pnl"],
            account["total_trades"],
        )

        logger.info(
            "BOT | "
            "candles=%s | "
            "BUY=%s | "
            "SELL=%s | "
            "HOLD=%s | "
            "REJECTED=%s",
            status["candles_processed"],
            status["buy_signals"],
            status["sell_signals"],
            status["hold_signals"],
            status["rejected_trades"],
        )


# ============================================================
# MAIN
# ============================================================

async def main():

    logger.info(
        "========================================"
    )

    logger.info(
        "STARTING ETH/USDT PAPER TRADING BOT"
    )

    logger.info(
        "========================================"
    )

    # --------------------------------------------------------
    # START BOT
    # --------------------------------------------------------

    bot.start()

    # --------------------------------------------------------
    # LOAD HISTORICAL DATA
    # --------------------------------------------------------

    await load_historical_data()

    # --------------------------------------------------------
    # WEBSOCKET
    # --------------------------------------------------------

    websocket_client = BinanceWebSocket(
        symbol=SYMBOL,
        on_trade=on_trade,
    )

    try:

        await asyncio.gather(
            websocket_client.connect(),
            status_loop(),
        )

    except asyncio.CancelledError:

        logger.info(
            "Bot cancelled."
        )

    finally:

        await websocket_client.stop()

        bot.stop()

        logger.info(
            "========================================"
        )

        logger.info(
            "FINAL BOT SUMMARY"
        )

        logger.info(
            "%s",
            bot.summary(),
        )

        logger.info(
            "========================================"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped by user."
        )
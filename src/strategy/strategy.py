import logging
from typing import Optional

from src.strategy.indicators import TechnicalIndicators


logger = logging.getLogger(__name__)


class TradingStrategy:
    """
    Initial ETH/USDT trading strategy.

    Uses:

        EMA 9
        EMA 21
        EMA 50
        RSI 14
        MACD
        Volume

    Returns:

        BUY
        SELL
        HOLD

    This class DOES NOT execute trades.
    """

    def __init__(
        self,
        minimum_candles: int = 50,
        volume_threshold: float = 1.0,
    ):
        self.minimum_candles = minimum_candles
        self.volume_threshold = volume_threshold

    def generate_signal(
        self,
        candles: list[dict],
    ) -> dict:

        if len(candles) < self.minimum_candles:

            return self._hold_signal(
                reason=(
                    f"Waiting for enough candles. "
                    f"{len(candles)}/{self.minimum_candles}"
                )
            )

        try:

            indicators = TechnicalIndicators(
                candles
            )

            data = indicators.calculate_all()

            if data.empty:

                return self._hold_signal(
                    "No indicator data available."
                )

            latest = data.iloc[-1]

            return self._evaluate(
                latest
            )

        except Exception as exc:

            logger.exception(
                "Strategy calculation failed: %s",
                exc,
            )

            return self._hold_signal(
                f"Strategy error: {exc}"
            )

    def _evaluate(
        self,
        row,
    ) -> dict:

        price = float(row["close"])

        ema_9 = row["ema_9"]
        ema_21 = row["ema_21"]
        ema_50 = row["ema_50"]

        rsi = row["rsi_14"]

        macd = row["macd"]
        macd_signal = row["macd_signal"]
        macd_histogram = row["macd_histogram"]

        volume_ratio = row["volume_ratio"]

        # Make sure indicators are ready.
        required = [
            ema_9,
            ema_21,
            ema_50,
            rsi,
            macd,
            macd_signal,
            macd_histogram,
            volume_ratio,
        ]

        if any(
            value is None
            for value in required
        ):

            return self._hold_signal(
                "Indicators are not ready.",
                price,
            )

        # Convert to floats.
        ema_9 = float(ema_9)
        ema_21 = float(ema_21)
        ema_50 = float(ema_50)

        rsi = float(rsi)

        macd = float(macd)
        macd_signal = float(macd_signal)
        macd_histogram = float(
            macd_histogram
        )

        volume_ratio = float(
            volume_ratio
        )

        buy_conditions = []
        sell_conditions = []

        # --------------------------------------------
        # TREND
        # --------------------------------------------

        bullish_trend = (
            ema_9 > ema_21
            and ema_21 > ema_50
        )

        bearish_trend = (
            ema_9 < ema_21
            and ema_21 < ema_50
        )

        if bullish_trend:

            buy_conditions.append(
                "EMA9 > EMA21 > EMA50"
            )

        if bearish_trend:

            sell_conditions.append(
                "EMA9 < EMA21 < EMA50"
            )

        # --------------------------------------------
        # RSI
        # --------------------------------------------

        bullish_rsi = (
            50 <= rsi < 70
        )

        bearish_rsi = (
            30 < rsi <= 50
        )

        if bullish_rsi:

            buy_conditions.append(
                f"RSI bullish ({rsi:.2f})"
            )

        if bearish_rsi:

            sell_conditions.append(
                f"RSI bearish ({rsi:.2f})"
            )

        # --------------------------------------------
        # MACD
        # --------------------------------------------

        bullish_macd = (
            macd > macd_signal
            and macd_histogram > 0
        )

        bearish_macd = (
            macd < macd_signal
            and macd_histogram < 0
        )

        if bullish_macd:

            buy_conditions.append(
                "MACD bullish"
            )

        if bearish_macd:

            sell_conditions.append(
                "MACD bearish"
            )

        # --------------------------------------------
        # VOLUME
        # --------------------------------------------

        strong_volume = (
            volume_ratio >= self.volume_threshold
        )

        if strong_volume:

            buy_conditions.append(
                f"Volume strong ({volume_ratio:.2f}x)"
            )

            sell_conditions.append(
                f"Volume strong ({volume_ratio:.2f}x)"
            )

        # --------------------------------------------
        # SIGNAL DECISION
        # --------------------------------------------

        buy_score = self._calculate_score(
            bullish_trend,
            bullish_rsi,
            bullish_macd,
            strong_volume,
        )

        sell_score = self._calculate_score(
            bearish_trend,
            bearish_rsi,
            bearish_macd,
            strong_volume,
        )

        # BUY requires trend + momentum confirmation.
        if (
            bullish_trend
            and bullish_macd
            and bullish_rsi
            and buy_score >= 3
        ):

            confidence = self._confidence(
                buy_score
            )

            return {
                "action": "BUY",
                "price": price,
                "confidence": confidence,
                "score": buy_score,
                "reason": buy_conditions,
                "indicators": self._indicator_snapshot(
                    row
                ),
            }

        # SELL requires trend + momentum confirmation.
        if (
            bearish_trend
            and bearish_macd
            and bearish_rsi
            and sell_score >= 3
        ):

            confidence = self._confidence(
                sell_score
            )

            return {
                "action": "SELL",
                "price": price,
                "confidence": confidence,
                "score": sell_score,
                "reason": sell_conditions,
                "indicators": self._indicator_snapshot(
                    row
                ),
            }

        return {
            "action": "HOLD",
            "price": price,
            "confidence": 0.0,
            "score": max(
                buy_score,
                sell_score,
            ),
            "reason": [
                "No strong trading setup."
            ],
            "indicators": self._indicator_snapshot(
                row
            ),
        }

    @staticmethod
    def _calculate_score(
        trend: bool,
        rsi: bool,
        macd: bool,
        volume: bool,
    ) -> int:

        score = 0

        if trend:
            score += 1

        if rsi:
            score += 1

        if macd:
            score += 1

        if volume:
            score += 1

        return score

    @staticmethod
    def _confidence(
        score: int,
    ) -> float:

        confidence_map = {
            0: 0.0,
            1: 0.25,
            2: 0.50,
            3: 0.75,
            4: 0.90,
        }

        return confidence_map.get(
            score,
            0.90,
        )

    @staticmethod
    def _indicator_snapshot(
        row,
    ) -> dict:

        return {
            "ema_9": TradingStrategy._safe_float(
                row["ema_9"]
            ),
            "ema_21": TradingStrategy._safe_float(
                row["ema_21"]
            ),
            "ema_50": TradingStrategy._safe_float(
                row["ema_50"]
            ),
            "rsi_14": TradingStrategy._safe_float(
                row["rsi_14"]
            ),
            "macd": TradingStrategy._safe_float(
                row["macd"]
            ),
            "macd_signal": TradingStrategy._safe_float(
                row["macd_signal"]
            ),
            "macd_histogram": TradingStrategy._safe_float(
                row["macd_histogram"]
            ),
            "volume_ratio": TradingStrategy._safe_float(
                row["volume_ratio"]
            ),
        }

    @staticmethod
    def _safe_float(
        value,
    ) -> Optional[float]:

        if value is None:
            return None

        try:

            return float(value)

        except (TypeError, ValueError):

            return None

    @staticmethod
    def _hold_signal(
        reason: str,
        price: Optional[float] = None,
    ) -> dict:

        return {
            "action": "HOLD",
            "price": price,
            "confidence": 0.0,
            "score": 0,
            "reason": [reason],
            "indicators": {},
        }
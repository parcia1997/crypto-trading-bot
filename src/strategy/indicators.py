import pandas as pd
import numpy as np


class TechnicalIndicators:
    """
    Technical indicator calculations for OHLCV candle data.

    Expected columns:

        timestamp
        open
        high
        low
        close
        volume
    """

    def __init__(self, candles: list[dict]):
        if not candles:
            raise ValueError("No candle data provided.")

        self.df = pd.DataFrame(candles)

        self._validate_data()

        self.df = self.df.sort_values(
            "timestamp"
        ).reset_index(drop=True)

    def _validate_data(self):
        required_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        missing = [
            column
            for column in required_columns
            if column not in self.df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        for column in required_columns:
            self.df[column] = pd.to_numeric(
                self.df[column],
                errors="coerce",
            )

        self.df.dropna(
            subset=required_columns,
            inplace=True,
        )

    # --------------------------------------------------
    # EMA
    # --------------------------------------------------

    def ema(
        self,
        period: int,
        column: str = "close",
    ) -> pd.Series:

        if period <= 0:
            raise ValueError(
                "EMA period must be greater than 0."
            )

        return self.df[column].ewm(
            span=period,
            adjust=False,
        ).mean()

    # --------------------------------------------------
    # RSI
    # --------------------------------------------------

    def rsi(
        self,
        period: int = 14,
        column: str = "close",
    ) -> pd.Series:

        if period <= 0:
            raise ValueError(
                "RSI period must be greater than 0."
            )

        delta = self.df[column].diff()

        gains = delta.clip(lower=0)

        losses = -delta.clip(upper=0)

        average_gain = gains.ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False,
        ).mean()

        average_loss = losses.ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False,
        ).mean()

        rs = average_gain / average_loss.replace(
            0,
            np.nan,
        )

        rsi = 100 - (
            100 / (1 + rs)
        )

        return rsi

    # --------------------------------------------------
    # MACD
    # --------------------------------------------------

    def macd(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> pd.DataFrame:

        fast_ema = self.ema(
            fast_period
        )

        slow_ema = self.ema(
            slow_period
        )

        macd_line = fast_ema - slow_ema

        signal_line = macd_line.ewm(
            span=signal_period,
            adjust=False,
        ).mean()

        histogram = (
            macd_line - signal_line
        )

        return pd.DataFrame(
            {
                "macd": macd_line,
                "macd_signal": signal_line,
                "macd_histogram": histogram,
            }
        )

    # --------------------------------------------------
    # ATR
    # --------------------------------------------------

    def atr(
        self,
        period: int = 14,
    ) -> pd.Series:

        previous_close = self.df[
            "close"
        ].shift(1)

        high_low = (
            self.df["high"]
            - self.df["low"]
        )

        high_previous_close = (
            self.df["high"]
            - previous_close
        ).abs()

        low_previous_close = (
            self.df["low"]
            - previous_close
        ).abs()

        true_range = pd.concat(
            [
                high_low,
                high_previous_close,
                low_previous_close,
            ],
            axis=1,
        ).max(axis=1)

        atr = true_range.ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False,
        ).mean()

        return atr

    # --------------------------------------------------
    # Volume Moving Average
    # --------------------------------------------------

    def volume_average(
        self,
        period: int = 20,
    ) -> pd.Series:

        return self.df["volume"].rolling(
            window=period
        ).mean()

    # --------------------------------------------------
    # Volume Ratio
    # --------------------------------------------------

    def volume_ratio(
        self,
        period: int = 20,
    ) -> pd.Series:

        average_volume = self.volume_average(
            period
        )

        return (
            self.df["volume"]
            / average_volume
        )

    # --------------------------------------------------
    # Add all indicators
    # --------------------------------------------------

    def calculate_all(self) -> pd.DataFrame:

        result = self.df.copy()

        # EMA
        result["ema_9"] = self.ema(9)

        result["ema_21"] = self.ema(21)

        result["ema_50"] = self.ema(50)

        # RSI
        result["rsi_14"] = self.rsi(14)

        # MACD
        macd_data = self.macd()

        result = pd.concat(
            [
                result,
                macd_data,
            ],
            axis=1,
        )

        # ATR
        result["atr_14"] = self.atr(14)

        # Volume
        result["volume_average_20"] = (
            self.volume_average(20)
        )

        result["volume_ratio"] = (
            self.volume_ratio(20)
        )

        return result

    # --------------------------------------------------
    # Latest indicator values
    # --------------------------------------------------

    def latest(self) -> dict:

        result = self.calculate_all()

        if result.empty:
            raise ValueError(
                "No valid candle data available."
            )

        latest = result.iloc[-1]

        return {
            "timestamp": latest["timestamp"],
            "price": float(latest["close"]),

            "ema_9": self._safe_float(
                latest["ema_9"]
            ),

            "ema_21": self._safe_float(
                latest["ema_21"]
            ),

            "ema_50": self._safe_float(
                latest["ema_50"]
            ),

            "rsi_14": self._safe_float(
                latest["rsi_14"]
            ),

            "macd": self._safe_float(
                latest["macd"]
            ),

            "macd_signal": self._safe_float(
                latest["macd_signal"]
            ),

            "macd_histogram": self._safe_float(
                latest["macd_histogram"]
            ),

            "atr_14": self._safe_float(
                latest["atr_14"]
            ),

            "volume": self._safe_float(
                latest["volume"]
            ),

            "volume_average_20": self._safe_float(
                latest["volume_average_20"]
            ),

            "volume_ratio": self._safe_float(
                latest["volume_ratio"]
            ),
        }

    @staticmethod
    def _safe_float(value):

        if pd.isna(value):
            return None

        return float(value)
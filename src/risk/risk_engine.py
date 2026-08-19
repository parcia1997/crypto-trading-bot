import logging
from typing import Optional


logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Risk management engine.

    Converts a strategy signal into a controlled
    trade proposal.

    This class DOES NOT execute orders.
    """

    def __init__(
        self,
        account_balance: float,
        risk_per_trade: float = 0.01,
        stop_loss_atr_multiplier: float = 1.0,
        take_profit_atr_multiplier: float = 2.0,
        max_position_percentage: float = 0.25,
        minimum_risk_reward: float = 2.0,
        minimum_position_size: float = 0.0001,
    ):
        if account_balance <= 0:
            raise ValueError(
                "Account balance must be greater than 0."
            )

        if not 0 < risk_per_trade <= 1:
            raise ValueError(
                "risk_per_trade must be between 0 and 1."
            )

        if stop_loss_atr_multiplier <= 0:
            raise ValueError(
                "Stop-loss ATR multiplier must be greater than 0."
            )

        if take_profit_atr_multiplier <= 0:
            raise ValueError(
                "Take-profit ATR multiplier must be greater than 0."
            )

        if not 0 < max_position_percentage <= 1:
            raise ValueError(
                "max_position_percentage must be between 0 and 1."
            )

        self.account_balance = account_balance

        self.risk_per_trade = risk_per_trade

        self.stop_loss_atr_multiplier = (
            stop_loss_atr_multiplier
        )

        self.take_profit_atr_multiplier = (
            take_profit_atr_multiplier
        )

        self.max_position_percentage = (
            max_position_percentage
        )

        self.minimum_risk_reward = (
            minimum_risk_reward
        )

        self.minimum_position_size = (
            minimum_position_size
        )

    def evaluate(
        self,
        signal: dict,
    ) -> dict:
        """
        Evaluate a strategy signal.

        Returns a trade proposal.

        No order is placed.
        """

        action = signal.get("action")

        if action not in {
            "BUY",
            "SELL",
            "HOLD",
        }:
            return self._rejected(
                "Invalid strategy action."
            )

        if action == "HOLD":
            return self._hold_result(
                signal
            )

        price = self._get_float(
            signal.get("price")
        )

        indicators = signal.get(
            "indicators",
            {},
        )

        atr = self._get_float(
            indicators.get("atr_14")
        )

        if price is None or price <= 0:
            return self._rejected(
                "Invalid entry price."
            )

        if atr is None or atr <= 0:
            return self._rejected(
                "ATR is not available."
            )

        return self._calculate_trade(
            action=action,
            entry_price=price,
            atr=atr,
            signal=signal,
        )
        def update_account_balance(
        self,
        account_balance: float,
        ):
            """
            Update the account balance used for risk calculations.
            """

        if account_balance <= 0:
            raise ValueError(
                "Account balance must be greater than 0."
            )

        self.account_balance = account_balance

        logger.info(
            "Risk engine balance updated: %.2f",
            account_balance,
        )

    def _calculate_trade(
        self,
        action: str,
        entry_price: float,
        atr: float,
        signal: dict,
    ) -> dict:
        """
        Calculate position size and price levels.
        """

        # ------------------------------------------
        # Maximum account risk
        # ------------------------------------------

        risk_amount = (
            self.account_balance
            * self.risk_per_trade
        )

        # ------------------------------------------
        # Stop-loss distance
        # ------------------------------------------

        stop_distance = (
            atr
            * self.stop_loss_atr_multiplier
        )

        if stop_distance <= 0:
            return self._rejected(
                "Invalid stop-loss distance."
            )

        # ------------------------------------------
        # Stop loss / Take profit
        # ------------------------------------------

        if action == "BUY":

            stop_loss = (
                entry_price
                - stop_distance
            )

            take_profit = (
                entry_price
                + (
                    atr
                    * self.take_profit_atr_multiplier
                )
            )

        else:

            stop_loss = (
                entry_price
                + stop_distance
            )

            take_profit = (
                entry_price
                - (
                    atr
                    * self.take_profit_atr_multiplier
                )
            )

        if stop_loss <= 0:
            return self._rejected(
                "Calculated stop-loss is invalid."
            )

        if take_profit <= 0:
            return self._rejected(
                "Calculated take-profit is invalid."
            )

        # ------------------------------------------
        # Risk / Reward
        # ------------------------------------------

        reward_distance = abs(
            take_profit - entry_price
        )

        risk_reward = (
            reward_distance
            / stop_distance
        )

        if risk_reward < self.minimum_risk_reward:

            return self._rejected(
                f"Risk/reward {risk_reward:.2f} "
                f"is below minimum "
                f"{self.minimum_risk_reward:.2f}."
            )

        # ------------------------------------------
        # Position size based on risk
        # ------------------------------------------

        position_size = (
            risk_amount
            / stop_distance
        )

        # ------------------------------------------
        # Maximum position value
        # ------------------------------------------

        max_position_value = (
            self.account_balance
            * self.max_position_percentage
        )

        max_position_size = (
            max_position_value
            / entry_price
        )

        # Limit position size.
        position_size = min(
            position_size,
            max_position_size,
        )

        if position_size < self.minimum_position_size:

            return self._rejected(
                "Calculated position size is too small."
            )

        # ------------------------------------------
        # Actual position value
        # ------------------------------------------

        position_value = (
            position_size
            * entry_price
        )

        # ------------------------------------------
        # Actual maximum loss
        # ------------------------------------------

        maximum_loss = (
            position_size
            * stop_distance
        )

        # ------------------------------------------
        # Confidence
        # ------------------------------------------

        confidence = self._get_float(
            signal.get("confidence")
        )

        if confidence is None:
            confidence = 0.0

        return {
            "approved": True,
            "action": action,

            "entry_price": entry_price,

            "position_size": position_size,

            "position_value": position_value,

            "risk_amount": risk_amount,

            "maximum_loss": maximum_loss,

            "stop_loss": stop_loss,

            "take_profit": take_profit,

            "risk_reward": risk_reward,

            "atr": atr,

            "confidence": confidence,

            "reason": signal.get(
                "reason",
                [],
            ),
        }

    def _hold_result(
        self,
        signal: dict,
    ) -> dict:

        return {
            "approved": False,
            "action": "HOLD",
            "entry_price": signal.get(
                "price"
            ),
            "position_size": 0.0,
            "position_value": 0.0,
            "risk_amount": 0.0,
            "maximum_loss": 0.0,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward": 0.0,
            "atr": None,
            "confidence": signal.get(
                "confidence",
                0.0,
            ),
            "reason": [
                "Strategy returned HOLD."
            ],
        }

    @staticmethod
    def _rejected(
        reason: str,
    ) -> dict:

        logger.warning(
            "Trade rejected: %s",
            reason,
        )

        return {
            "approved": False,
            "action": "REJECTED",
            "entry_price": None,
            "position_size": 0.0,
            "position_value": 0.0,
            "risk_amount": 0.0,
            "maximum_loss": 0.0,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward": 0.0,
            "atr": None,
            "confidence": 0.0,
            "reason": [reason],
        }

    @staticmethod
    def _get_float(
        value: Optional[float],
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None
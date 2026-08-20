import logging
from typing import Optional


logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Fee-aware risk management engine.

    Responsibilities:

    - Position sizing
    - Stop loss
    - Take profit
    - Risk/reward validation
    - Maximum position limit
    - BUY fee estimation
    - SELL fee estimation
    - Slippage estimation
    - Expected gross profit
    - Expected net profit
    - Reject trades where expected profit
      does not cover trading costs

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

        # ------------------------------------------
        # Trading costs
        # ------------------------------------------

        fee_rate: float = 0.001,

        estimated_slippage_rate: float = 0.0,

        minimum_expected_net_profit: float = 0.0,
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

        if fee_rate < 0:
            raise ValueError(
                "fee_rate cannot be negative."
            )

        if estimated_slippage_rate < 0:
            raise ValueError(
                "estimated_slippage_rate cannot be negative."
            )

        if minimum_expected_net_profit < 0:
            raise ValueError(
                "minimum_expected_net_profit cannot be negative."
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

        # ------------------------------------------
        # Trading cost configuration
        # ------------------------------------------

        self.fee_rate = fee_rate

        self.estimated_slippage_rate = (
            estimated_slippage_rate
        )

        self.minimum_expected_net_profit = (
            minimum_expected_net_profit
        )

    # ==================================================
    # UPDATE ACCOUNT BALANCE
    # ==================================================

    def update_account_balance(
        self,
        account_balance: float,
    ):
        """
        Update the account balance used
        for future position sizing.
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

    # ==================================================
    # EVALUATE SIGNAL
    # ==================================================

    def evaluate(
        self,
        signal: dict,
    ) -> dict:
        """
        Evaluate BUY / SELL / HOLD signal.
        """

        action = signal.get(
            "action"
        )

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

    # ==================================================
    # CALCULATE TRADE
    # ==================================================

    def _calculate_trade(
        self,
        action: str,
        entry_price: float,
        atr: float,
        signal: dict,
    ) -> dict:
        """
        Calculate risk, position size, fees,
        expected profit and expected net profit.
        """

        # ------------------------------------------
        # Risk amount
        # ------------------------------------------

        risk_amount = (
            self.account_balance
            * self.risk_per_trade
        )

        # ------------------------------------------
        # Stop distance
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
        # Stop Loss / Take Profit
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
            take_profit
            - entry_price
        )

        risk_reward = (
            reward_distance
            / stop_distance
        )

        if (
            risk_reward
            < self.minimum_risk_reward
        ):

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
        # Maximum allowed position
        # ------------------------------------------

        max_position_value = (
            self.account_balance
            * self.max_position_percentage
        )

        max_position_size = (
            max_position_value
            / entry_price
        )

        position_size = min(
            position_size,
            max_position_size,
        )

        if (
            position_size
            < self.minimum_position_size
        ):

            return self._rejected(
                "Calculated position size is too small."
            )

        # ------------------------------------------
        # Position value
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

        # ==================================================
        # FEE-AWARE CALCULATION
        # ==================================================

        # ------------------------------------------
        # Entry fee
        # ------------------------------------------

        entry_fee = (
            position_value
            * self.fee_rate
        )

        # ------------------------------------------
        # Expected exit value at Take Profit
        # ------------------------------------------

        expected_exit_value = (
            position_size
            * take_profit
        )

        # ------------------------------------------
        # Exit fee
        # ------------------------------------------

        exit_fee = (
            expected_exit_value
            * self.fee_rate
        )

        # ------------------------------------------
        # Total trading fees
        # ------------------------------------------

        total_fees = (
            entry_fee
            + exit_fee
        )

        # ------------------------------------------
        # Estimated slippage
        #
        # Estimated on both entry and exit.
        # ------------------------------------------

        entry_slippage = (
            position_value
            * self.estimated_slippage_rate
        )

        exit_slippage = (
            expected_exit_value
            * self.estimated_slippage_rate
        )

        total_slippage = (
            entry_slippage
            + exit_slippage
        )

        # ------------------------------------------
        # Expected gross profit at TP
        # ------------------------------------------

        expected_gross_profit = (
            reward_distance
            * position_size
        )

        # ------------------------------------------
        # Expected net profit
        # ------------------------------------------

        expected_net_profit = (
            expected_gross_profit
            - total_fees
            - total_slippage
        )

        # ------------------------------------------
        # Break-even percentage
        # ------------------------------------------

        if position_value > 0:

            trading_cost_percentage = (
                (
                    total_fees
                    + total_slippage
                )
                / position_value
            ) * 100

        else:

            trading_cost_percentage = 0.0

        # ------------------------------------------
        # Expected gross return %
        # ------------------------------------------

        expected_gross_return_percentage = (
            reward_distance
            / entry_price
        ) * 100

        # ------------------------------------------
        # Expected net return %
        # ------------------------------------------

        if position_value > 0:

            expected_net_return_percentage = (
                expected_net_profit
                / position_value
            ) * 100

        else:

            expected_net_return_percentage = 0.0

        # ==================================================
        # REJECT UNPROFITABLE TRADE
        # ==================================================

        if (
            expected_net_profit
            <= self.minimum_expected_net_profit
        ):

            return self._rejected(
                (
                    "Expected profit does not cover "
                    "fees/slippage sufficiently. "
                    f"Gross profit={expected_gross_profit:.4f}, "
                    f"fees={total_fees:.4f}, "
                    f"slippage={total_slippage:.4f}, "
                    f"net profit={expected_net_profit:.4f}"
                )
            )

        # ------------------------------------------
        # Confidence
        # ------------------------------------------

        confidence = self._get_float(
            signal.get("confidence")
        )

        if confidence is None:
            confidence = 0.0

        # ==================================================
        # APPROVED
        # ==================================================

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

            # --------------------------------------
            # Fee-aware information
            # --------------------------------------

            "fee_rate": self.fee_rate,

            "entry_fee": entry_fee,

            "exit_fee": exit_fee,

            "total_fees": total_fees,

            "estimated_slippage": (
                total_slippage
            ),

            "expected_gross_profit": (
                expected_gross_profit
            ),

            "expected_net_profit": (
                expected_net_profit
            ),

            "trading_cost_percentage": (
                trading_cost_percentage
            ),

            "expected_gross_return_percentage": (
                expected_gross_return_percentage
            ),

            "expected_net_return_percentage": (
                expected_net_return_percentage
            ),

            "reason": signal.get(
                "reason",
                [],
            ),
        }

    # ==================================================
    # HOLD
    # ==================================================

    def _hold_result(
        self,
        signal: dict,
    ) -> dict:

        return {
            "approved": False,

            "action": "HOLD",

            "entry_price":
                signal.get("price"),

            "position_size": 0.0,

            "position_value": 0.0,

            "risk_amount": 0.0,

            "maximum_loss": 0.0,

            "stop_loss": None,

            "take_profit": None,

            "risk_reward": 0.0,

            "atr": None,

            "confidence":
                signal.get(
                    "confidence",
                    0.0,
                ),

            "reason": [
                "Strategy returned HOLD."
            ],
        }

    # ==================================================
    # REJECT
    # ==================================================

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

            "reason": [
                reason
            ],
        }

    # ==================================================
    # SAFE FLOAT
    # ==================================================

    @staticmethod
    def _get_float(
        value: Optional[float],
    ) -> Optional[float]:

        if value is None:
            return None

        try:

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return None
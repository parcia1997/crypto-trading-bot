import logging
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class RiskGuard:
    """
    Protects the trading bot from excessive losses.

    Protections:

    1. Maximum daily loss
    2. Maximum consecutive losses

    The guard does NOT execute or close trades.
    It only decides whether a NEW trade is allowed.
    """

    def __init__(
        self,
        starting_balance: float,
        max_daily_loss_percentage: float = 0.03,
        max_consecutive_losses: int = 3,
    ):
        if starting_balance <= 0:
            raise ValueError(
                "Starting balance must be greater than 0."
            )

        if not 0 < max_daily_loss_percentage <= 1:
            raise ValueError(
                "Daily loss percentage must be between 0 and 1."
            )

        if max_consecutive_losses <= 0:
            raise ValueError(
                "Maximum consecutive losses must be greater than 0."
            )

        self.starting_balance = starting_balance

        self.max_daily_loss_percentage = (
            max_daily_loss_percentage
        )

        self.max_consecutive_losses = (
            max_consecutive_losses
        )

        self.daily_loss_limit = (
            starting_balance
            * max_daily_loss_percentage
        )

        self.current_day = (
            datetime.now(timezone.utc).date()
        )

        self.day_start_equity = starting_balance

        self.consecutive_losses = 0

    # --------------------------------------------------
    # DAILY RESET
    # --------------------------------------------------

    def reset_if_new_day(
        self,
        current_equity: float,
    ):
        """
        Reset daily protection when a new UTC day begins.
        """

        today = datetime.now(
            timezone.utc
        ).date()

        if today != self.current_day:

            self.current_day = today

            self.day_start_equity = current_equity

            self.consecutive_losses = 0

            logger.info(
                "New trading day detected. "
                "Risk protection reset. "
                "Starting equity: %.2f",
                current_equity,
            )

    # --------------------------------------------------
    # DAILY P&L
    # --------------------------------------------------

    def daily_pnl(
        self,
        current_equity: float,
    ) -> float:
        """
        Calculate today's P&L.
        """

        self.reset_if_new_day(
            current_equity
        )

        return (
            current_equity
            - self.day_start_equity
        )

    # --------------------------------------------------
    # DAILY LOSS
    # --------------------------------------------------

    def daily_loss(
        self,
        current_equity: float,
    ) -> float:
        """
        Return today's loss as a positive number.
        """

        pnl = self.daily_pnl(
            current_equity
        )

        if pnl >= 0:
            return 0.0

        return abs(pnl)

    # --------------------------------------------------
    # RECORD TRADE RESULT
    # --------------------------------------------------

    def record_trade_result(
        self,
        net_pnl: float,
    ):
        """
        Record the result of a completed trade.

        Winning trade:
            consecutive losses reset to 0

        Losing trade:
            consecutive losses increase by 1
        """

        if net_pnl > 0:

            self.consecutive_losses = 0

            logger.info(
                "RISK GUARD | Winning trade | "
                "Consecutive losses reset."
            )

        elif net_pnl < 0:

            self.consecutive_losses += 1

            logger.warning(
                "RISK GUARD | Losing trade | "
                "Consecutive losses: %s/%s",
                self.consecutive_losses,
                self.max_consecutive_losses,
            )

    # --------------------------------------------------
    # CHECK WHETHER NEW TRADE IS ALLOWED
    # --------------------------------------------------

    def can_open_trade(
        self,
        current_equity: float,
    ) -> bool:
        """
        Determine whether a new trade is allowed.
        """

        # Check daily loss first.
        loss = self.daily_loss(
            current_equity
        )

        if loss >= self.daily_loss_limit:

            logger.warning(
                "DAILY LOSS LIMIT REACHED | "
                "loss=%.2f | limit=%.2f",
                loss,
                self.daily_loss_limit,
            )

            return False

        # Check consecutive losses.
        if (
            self.consecutive_losses
            >= self.max_consecutive_losses
        ):

            logger.warning(
                "CONSECUTIVE LOSS LIMIT REACHED | "
                "losses=%s | limit=%s",
                self.consecutive_losses,
                self.max_consecutive_losses,
            )

            return False

        return True

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def status(
        self,
        current_equity: float,
    ) -> dict:
        """
        Return current risk protection status.
        """

        pnl = self.daily_pnl(
            current_equity
        )

        loss = max(
            0.0,
            -pnl,
        )

        remaining_loss = max(
            0.0,
            self.daily_loss_limit - loss,
        )

        return {
            "current_day":
                str(self.current_day),

            "day_start_equity":
                self.day_start_equity,

            "current_equity":
                current_equity,

            "daily_pnl":
                pnl,

            "daily_loss":
                loss,

            "daily_loss_limit":
                self.daily_loss_limit,

            "remaining_loss":
                remaining_loss,

            "consecutive_losses":
                self.consecutive_losses,

            "max_consecutive_losses":
                self.max_consecutive_losses,

            "trading_allowed":
                (
                    loss < self.daily_loss_limit
                    and
                    self.consecutive_losses
                    < self.max_consecutive_losses
                ),
        }
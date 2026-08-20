from typing import List


class BacktestMetrics:
    """
    Calculates performance metrics from completed trades.
    """

    @staticmethod
    def calculate(
        trades: List,
        starting_balance: float,
        ending_equity: float,
    ) -> dict:

        total_trades = len(trades)

        if total_trades == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "net_profit": ending_equity - starting_balance,
                "profit_factor": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "total_fees": 0.0,
                "return_percentage": (
                    (ending_equity - starting_balance)
                    / starting_balance
                ) * 100,
            }

        winning_trades = [
            trade
            for trade in trades
            if trade.net_pnl > 0
        ]

        losing_trades = [
            trade
            for trade in trades
            if trade.net_pnl < 0
        ]

        gross_profit = sum(
            trade.net_pnl
            for trade in winning_trades
        )

        gross_loss = abs(
            sum(
                trade.net_pnl
                for trade in losing_trades
            )
        )

        total_fees = sum(
            trade.fees
            for trade in trades
        )

        net_profit = (
            ending_equity
            - starting_balance
        )

        win_rate = (
            len(winning_trades)
            / total_trades
        ) * 100

        if gross_loss > 0:
            profit_factor = (
                gross_profit
                / gross_loss
            )
        else:
            profit_factor = (
                float("inf")
                if gross_profit > 0
                else 0.0
            )

        average_win = (
            gross_profit
            / len(winning_trades)
            if winning_trades
            else 0.0
        )

        average_loss = (
            gross_loss
            / len(losing_trades)
            if losing_trades
            else 0.0
        )

        return_percentage = (
            net_profit
            / starting_balance
        ) * 100

        return {
            "total_trades":
                total_trades,

            "winning_trades":
                len(winning_trades),

            "losing_trades":
                len(losing_trades),

            "win_rate":
                win_rate,

            "gross_profit":
                gross_profit,

            "gross_loss":
                gross_loss,

            "net_profit":
                net_profit,

            "profit_factor":
                profit_factor,

            "average_win":
                average_win,

            "average_loss":
                average_loss,

            "total_fees":
                total_fees,

            "return_percentage":
                return_percentage,
        }
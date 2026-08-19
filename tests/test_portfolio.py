from src.portfolio.portfolio import Portfolio


def test_open_position():

    portfolio = Portfolio(
        starting_balance=1000.0
    )

    success = portfolio.open_position(
        quantity=0.1,
        price=4000.0,
        fee=0.0,
    )

    assert success is True

    assert portfolio.has_position()

    assert portfolio.cash == 600.0

    assert portfolio.quantity == 0.1

    assert portfolio.entry_price == 4000.0


def test_unrealized_profit():

    portfolio = Portfolio(
        starting_balance=1000.0
    )

    portfolio.open_position(
        quantity=0.1,
        price=4000.0,
    )

    portfolio.update_price(4020.0)

    assert portfolio.unrealized_pnl() == 2.0

    assert portfolio.equity() == 1002.0


def test_close_profitable_position():

    portfolio = Portfolio(
        starting_balance=1000.0
    )

    portfolio.open_position(
        quantity=0.1,
        price=4000.0,
    )

    pnl = portfolio.close_position(
        price=4040.0,
    )

    assert pnl == 4.0

    assert portfolio.realized_pnl == 4.0

    assert portfolio.cash == 1004.0

    assert portfolio.total_trades == 1

    assert portfolio.winning_trades == 1

    assert portfolio.losing_trades == 0

    assert portfolio.win_rate() == 1.0


def test_close_losing_position():

    portfolio = Portfolio(
        starting_balance=1000.0
    )

    portfolio.open_position(
        quantity=0.1,
        price=4000.0,
    )

    pnl = portfolio.close_position(
        price=3980.0,
    )

    assert pnl == -2.0

    assert portfolio.realized_pnl == -2.0

    assert portfolio.cash == 998.0

    assert portfolio.total_trades == 1

    assert portfolio.winning_trades == 0

    assert portfolio.losing_trades == 1


def test_win_rate():

    portfolio = Portfolio(
        starting_balance=1000.0
    )

    # Trade 1: win
    portfolio.open_position(
        quantity=0.1,
        price=4000.0,
    )

    portfolio.close_position(
        price=4020.0,
    )

    # Trade 2: loss
    portfolio.open_position(
        quantity=0.1,
        price=4000.0,
    )

    portfolio.close_position(
        price=3990.0,
    )

    assert portfolio.total_trades == 2

    assert portfolio.winning_trades == 1

    assert portfolio.losing_trades == 1

    assert portfolio.win_rate() == 0.5
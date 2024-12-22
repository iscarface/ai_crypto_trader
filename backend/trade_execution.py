import os
from datetime import datetime

from models import Trade

STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 5)) / 100
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 10)) / 100
RISK_PERCENT = float(os.getenv("RISK_PERCENT", 1)) / 100
BALANCE = 1000


def calculate_position_size(balance, entry_price, stop_loss_percent):
    """
    Calculate position size based on balance, entry price, and stop-loss percent.
    """
    entry_price = float(entry_price)  # Ensure entry_price is a float
    stop_loss_distance = stop_loss_percent * entry_price
    position_size = (balance * RISK_PERCENT) / stop_loss_distance
    return round(position_size, 6)  # Round to 6 decimals for precision


def buy_process(symbol, ticker, session, binance, quantity=None):
    """
    Handles the process of buying a trade.
    """
    existing_trade = (
        session.query(Trade)
        .filter(Trade.symbol == symbol, Trade.action == "BUY", Trade.exit_price == None)
        .first()
    )

    if existing_trade:
        print(f"Skipping duplicate BUY trade for {symbol}")
        return existing_trade

    balance = BALANCE
    entry_price = float(ticker["last"])  # Ensure entry_price is a float
    position_size = calculate_position_size(balance, entry_price, STOP_LOSS_PERCENT)

    if quantity:
        position_size = quantity  # Override with provided quantity

    trade = Trade(
        symbol=symbol,
        action="BUY",
        entry_price=entry_price,
        quantity=position_size,
        stop_loss_price=entry_price * (1 - STOP_LOSS_PERCENT),
        take_profit_price=entry_price * (1 + TAKE_PROFIT_PERCENT),
        timestamp=datetime.now(),
    )
    session.add(trade)
    session.commit()
    return trade


def sell_process(symbol, ticker, session):
    """
    Handles the process of selling a trade.
    """
    trade = (
        session.query(Trade)
        .filter(Trade.symbol == symbol, Trade.action == "BUY", Trade.exit_price == None)
        .first()
    )

    if not trade:
        raise ValueError(f"No active BUY trade for {symbol} to SELL.")

    current_price = ticker["last"]
    trade.exit_price = current_price
    trade.profit_loss = (current_price - trade.entry_price) * trade.quantity
    trade.timestamp = datetime.now()
    session.commit()
    return trade


def check_stop_loss_take_profit(trade, current_price, session):
    """
    Check if trade hits stop-loss or take-profit.
    """
    if current_price <= trade.stop_loss_price:
        trade.exit_price = trade.stop_loss_price
        trade.profit_loss = (trade.exit_price - trade.entry_price) * trade.quantity
        trade.timestamp = datetime.now()
        session.commit()
        return "STOP_LOSS"

    if current_price >= trade.take_profit_price:
        trade.exit_price = trade.take_profit_price
        trade.profit_loss = (trade.exit_price - trade.entry_price) * trade.quantity
        trade.timestamp = datetime.now()
        session.commit()
        return "TAKE_PROFIT"

    return None


def execute_trade(action, symbol, ticker, session, binance, quantity=None):
    """
    Unified function to handle both BUY and SELL trades.
    """
    if action == "BUY":
        return buy_process(symbol, ticker, session, binance)
    elif action == "SELL":
        return sell_process(symbol, ticker, session)
    else:
        raise ValueError(f"Invalid trade action: {action}")

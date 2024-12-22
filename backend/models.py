from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)  # buy, sell, hold
    entry_price = Column(Float, nullable=True)  # Entry price
    exit_price = Column(Float, nullable=True)  # Exit price
    quantity = Column(Float, nullable=False)
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    close_timestamp = Column(DateTime, nullable=True)


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    short_term = Column(Integer, nullable=False)
    long_term = Column(Integer, nullable=False)
    total_trades = Column(Integer, nullable=False)
    total_profit_loss_percentage = Column(Float, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

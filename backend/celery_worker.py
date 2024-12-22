import os
import time
import pandas as pd

from binance import Client
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from trade_execution import execute_trade

# Create Celery app
celery_app = Celery(
    "trading_bot",
    broker="redis://redis:6379/0",  # Redis URL as the message broker
    backend="redis://redis:6379/0",  # Redis for result storage
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "execute-trading-strategy-every-minute": {
        "task": "celery_worker.execute_periodic_trading",
        "schedule": crontab(minute="*/3"),  # Every minute
    },
}

load_dotenv()

binance = Client(
    api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET")
)

# Load strategy parameters from .env
SHORT_TERM_MA = int(os.getenv("SHORT_TERM_MA", 10))  # Default to 10 if not set
LONG_TERM_MA = int(os.getenv("LONG_TERM_MA", 50))  # Default to 50 if not set

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task()
def fetch_market_data(symbol: str):
    """
    Fetch live market data (OHLCV) for a given symbol.
    """
    ohlcv = binance.get_klines(symbol=symbol, interval="1h", limit=50)

    # Slice the first 6 columns (timestamp, open, high, low, close, volume)
    ohlcv = [row[:6] for row in ohlcv]

    # Create DataFrame with the appropriate column names
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    # Convert timestamp to a readable datetime format
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    return df.to_dict(orient="records")  # Return data as a dictionary


@celery_app.task
def execute_trading_strategy(symbol: str):
    """
    Execute a trading strategy and return JSON-serializable results.
    """
    # Fetch live market data
    ohlcv = fetch_market_data(symbol)
    df = pd.DataFrame(ohlcv)

    # Calculate moving averages
    df["short_ma"] = df["close"].rolling(window=SHORT_TERM_MA).mean()
    df["long_ma"] = df["close"].rolling(window=LONG_TERM_MA).mean()

    with SessionLocal() as session:
        if (
            df["short_ma"].iloc[-1] > df["long_ma"].iloc[-1]
            and df["short_ma"].iloc[-2] <= df["long_ma"].iloc[-2]
        ):
            ticker = {"last": float(df["close"].iloc[-1])}  # Simulated ticker
            trade = execute_trade(
                "BUY", symbol, ticker, session=session, binance=binance, quantity=1
            )

            # Convert Trade object to dictionary
            return {
                "symbol": trade.symbol,
                "action": trade.action,
                "entry_price": trade.entry_price,
                "quantity": trade.quantity,
                "timestamp": trade.timestamp.isoformat(),  # Convert datetime to string
                "stop_loss_price": trade.stop_loss_price,
                "take_profit_price": trade.take_profit_price,
            }
        elif (
            df["short_ma"].iloc[-1] < df["long_ma"].iloc[-1]
            and df["short_ma"].iloc[-2] >= df["long_ma"].iloc[-2]
        ):
            ticker = {"last": float(df["close"].iloc[-1])}  # Simulated ticker
            trade = execute_trade(
                "SELL", symbol, ticker, session=session, binance=binance
            )

            # Convert Trade object to dictionary
            return {
                "symbol": trade.symbol,
                "action": trade.action,
                "exit_price": trade.exit_price,
                "profit_loss": trade.profit_loss,
                "timestamp": trade.timestamp.isoformat(),  # Convert datetime to string
            }
        else:
            return {"message": "No trade signal detected."}


@celery_app.task
def execute_periodic_trading():
    """
    Periodically execute trading strategies for predefined symbols.
    """
    symbols = ["BTCUSDT", "ETHUSDT"]  # Add your trading pairs here
    for symbol in symbols:
        execute_trading_strategy.delay(symbol)
        time.sleep(2)

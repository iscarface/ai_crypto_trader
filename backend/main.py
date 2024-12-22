import os, sys
from datetime import datetime
from typing import List
import ccxt
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, Trade, BacktestResult
from strategies import moving_average_crossover
from schemas import TradeResponse
from trade_execution import check_stop_loss_take_profit, buy_process, sell_process


load_dotenv()


app = FastAPI()

# Database connection
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure all tables are created (initialization will use Alembic migrations)
Base.metadata.create_all(bind=engine)

# Binance connection
binance = ccxt.binance({"apiKey": API_KEY, "secret": API_SECRET})


@app.get("/status")
async def status():
    return {"message": "Trading bot is running!"}


@app.get("/simulate")
async def simulate_trading():
    """
    Simulate trading for the top 10 profitable trading pairs based on moving average crossover.
    Includes Stop-Loss, Take-Profit, and position sizing.
    """
    tickers = binance.fetch_tickers()
    sorted_tickers = sorted(
        [
            {"symbol": symbol, "change": ticker["percentage"]}
            for symbol, ticker in tickers.items()
            if "USDT" in symbol and ticker["percentage"] is not None
        ],
        key=lambda x: x["change"],
        reverse=True,
    )
    top_pairs = sorted_tickers[:10]
    simulated_trades = []

    with SessionLocal() as session:
        for pair in top_pairs:
            symbol = pair["symbol"]
            action = moving_average_crossover(symbol, binance, 5, 10)

            if action == "hold":
                continue

            ticker = binance.fetch_ticker(symbol)

            if action == "BUY":
                try:
                    trade = buy_process(symbol, ticker, session, binance)
                    simulated_trades.append(
                        {
                            "symbol": trade.symbol,
                            "action": trade.action,
                            "entry_price": trade.entry_price,
                            "quantity": trade.quantity,
                            "stop_loss_price": trade.stop_loss_price,
                            "take_profit_price": trade.take_profit_price,
                            "status": "OPEN",
                        }
                    )
                except Exception as e:
                    print(f"Error during BUY process for {symbol}: {e}")

            elif action == "SELL":
                try:
                    trade = sell_process(symbol, ticker, session)
                    simulated_trades.append(
                        {
                            "symbol": trade.symbol,
                            "action": "SELL",
                            "entry_price": trade.entry_price,
                            "exit_price": trade.exit_price,
                            "profit_loss": trade.profit_loss,
                            "quantity": trade.quantity,
                            "status": "CLOSED",
                        }
                    )
                except ValueError as e:
                    print(f"Error during SELL process for {symbol}: {e}")

    return {"message": "Simulation complete.", "simulated_trades": simulated_trades}


@app.get("/trades", response_model=List[TradeResponse])
async def get_trades():
    with SessionLocal() as session:
        trades = session.query(Trade).all()

    # Deduplicate trades based on symbol and timestamp
    unique_trades = {
        f"{trade.symbol}_{trade.timestamp}": trade for trade in trades
    }.values()

    response = [TradeResponse.from_orm(trade) for trade in unique_trades]
    return response


@app.get("/performance")
async def get_performance():
    with SessionLocal() as session:
        # Fetch all trades sorted by timestamp
        trades = session.query(Trade).order_by(Trade.timestamp).all()

    # Generate performance data
    performance_data = []
    portfolio_value = 1000  # Starting portfolio value
    for trade in trades:
        if trade.profit_loss is not None:
            portfolio_value += (
                trade.profit_loss
            )  # Adjust portfolio value by profit/loss

        performance_data.append(
            {
                "timestamp": trade.timestamp.isoformat(),  # Use ISO format for frontend compatibility
                "portfolio_value": round(portfolio_value, 2),
                "profit_loss": trade.profit_loss
                or 0,  # Default to 0 if profit_loss is None
            }
        )

    return performance_data


@app.get("/backtest")
async def backtest_trading(
    symbol: str = "BTC/USDT",
    short_term: int = 10,
    long_term: int = 50,
    initial_balance: float = 10000.0,
    stop_loss_percent: float = 0.05,
    take_profit_percent: float = 0.1,
):
    """
    Backtest a trading strategy using historical data.
    """
    # Fetch historical OHLCV data
    ohlcv = binance.fetch_ohlcv(symbol, timeframe="1h", limit=long_term * 5)
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    # Calculate moving averages
    df["short_ma"] = df["close"].rolling(window=short_term).mean()
    df["long_ma"] = df["close"].rolling(window=long_term).mean()

    # Initialize variables for simulation
    balance = initial_balance
    position = None
    entry_price = 0
    trades = []

    for i in range(long_term, len(df)):
        # Check for buy/sell signals
        if (
            df["short_ma"][i] > df["long_ma"][i]
            and df["short_ma"][i - 1] <= df["long_ma"][i - 1]
        ):
            if not position:
                # Buy signal
                entry_price = df["close"][i]
                position = "long"
                continue

        if (
            df["short_ma"][i] < df["long_ma"][i]
            and df["short_ma"][i - 1] >= df["long_ma"][i - 1]
        ):
            if position == "long":
                # Sell signal
                exit_price = df["close"][i]
                profit_loss = (exit_price - entry_price) / entry_price * 100
                balance += balance * (profit_loss / 100)
                trades.append(
                    {
                        "entry": entry_price,
                        "exit": exit_price,
                        "profit_loss": profit_loss,
                    }
                )
                position = None

    # Calculate performance metrics
    total_trades = len(trades)
    total_profit_loss = sum([t["profit_loss"] for t in trades])
    winning_trades = len([t for t in trades if t["profit_loss"] > 0])
    losing_trades = total_trades - winning_trades

    return {
        "symbol": symbol,
        "short_term": short_term,
        "long_term": long_term,
        "initial_balance": initial_balance,
        "final_balance": round(balance, 2),
        "total_trades": total_trades,
        "total_profit_loss": round(total_profit_loss, 2),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "trades": trades,
    }


@app.get("/backtest-results")
async def get_backtest_results():
    session = SessionLocal()
    results = session.query(BacktestResult).all()
    session.close()
    return [
        {
            "id": result.id,
            "symbol": result.symbol,
            "short_term": result.short_term,
            "long_term": result.long_term,
            "total_trades": result.total_trades,
            "total_profit_loss_percentage": result.total_profit_loss_percentage,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "created_at": result.created_at,
        }
        for result in results
    ]


@app.post("/monitor")
async def monitor_active_trades():
    """
    Monitor active trades and close if Stop-Loss or Take-Profit is hit.
    """
    session = SessionLocal()
    active_trades = session.query(Trade).filter(Trade.exit_price == None).all()
    for trade in active_trades:
        ticker = binance.fetch_ticker(trade.symbol)
        current_price = ticker["last"]

        result = check_stop_loss_take_profit(trade, current_price, session)
        if result:
            print(
                f"Trade {trade.id} closed due to {result} at price {trade.exit_price}."
            )
    session.close()
    return {"message": "Monitoring complete."}

import random
import pandas as pd


def moving_average_crossover(
    symbol, binance, short_term=5, long_term=10, simulate=True
):
    """
    Moving Average Crossover Strategy for simulation and live testing.
    """
    if simulate:
        # Generate random signals for testing
        return random.choice(["BUY", "SELL", "hold"])

    # Fetch historical OHLCV data (live mode)
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe="1h", limit=long_term * 2)
        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Calculate moving averages
        df["short_ma"] = df["close"].rolling(window=short_term).mean()
        df["long_ma"] = df["close"].rolling(window=long_term).mean()

        # Check for crossover
        if len(df) >= long_term + 1:
            if (
                df["short_ma"].iloc[-1] > df["long_ma"].iloc[-1]
                and df["short_ma"].iloc[-2] <= df["long_ma"].iloc[-2]
            ):
                return "BUY"
            elif (
                df["short_ma"].iloc[-1] < df["long_ma"].iloc[-1]
                and df["short_ma"].iloc[-2] >= df["long_ma"].iloc[-2]
            ):
                return "SELL"
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")

    # Default to HOLD if no signal
    return "hold"

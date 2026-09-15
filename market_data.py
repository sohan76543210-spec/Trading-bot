import requests
import pandas as pd


BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_klines(symbol="BTCUSDT", interval="15m", limit=500):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BINANCE_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    columns = [
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]

    df = pd.DataFrame(data, columns=columns)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    return df

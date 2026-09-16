import requests
import pandas as pd


COINBASE_URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"


def get_klines(symbol="BTCUSDT", interval="15m", limit=300):

    granularity_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "1d": 86400
    }

    granularity = granularity_map.get(interval, 900)

    params = {
        "granularity": granularity
    }

    response = requests.get(
        COINBASE_URL,
        params=params,
        timeout=20,
        headers={
            "User-Agent": "Trading-Bot/1.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise RuntimeError("Coinbase returned no market data.")

    # Coinbase:
    # [time, low, high, open, close, volume]

    df = pd.DataFrame(
        data,
        columns=[
            "time",
            "low",
            "high",
            "open",
            "close",
            "volume"
        ]
    )

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.sort_values("time")
    df = df.dropna()
    df = df.reset_index(drop=True)

    # Coinbase ignores an explicit "limit" query param and just returns up
    # to 300 candles, so we trim to the caller's requested amount here.
    if limit and len(df) > limit:
        df = df.iloc[-limit:].reset_index(drop=True)

    if len(df) < 200:
        raise RuntimeError(
            f"Only {len(df)} candles returned for {symbol} {interval}; "
            "need at least 200 for EMA200/indicator calculations."
        )

    return df

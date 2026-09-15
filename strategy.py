import pandas as pd


def add_indicators(df):
    df = df.copy()

    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    df["atr"] = calculate_atr(df, 14)

    df["volume_ma"] = df["volume"].rolling(20).mean()

    return df


def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    return tr.rolling(period).mean()


def liquidity_sweep(df, lookback=20):
    previous_high = df["high"].shift(1).rolling(lookback).max()
    previous_low = df["low"].shift(1).rolling(lookback).min()

    bullish_sweep = (
        (df["low"] < previous_low) &
        (df["close"] > previous_low)
    )

    bearish_sweep = (
        (df["high"] > previous_high) &
        (df["close"] < previous_high)
    )

    return bullish_sweep, bearish_sweep


def market_structure(df):
    previous_high = df["high"].shift(1)
    previous_low = df["low"].shift(1)

    bullish = df["close"] > previous_high
    bearish = df["close"] < previous_low

    return bullish, bearish


def displacement(df):
    candle_body = abs(df["close"] - df["open"])

    average_body = candle_body.rolling(20).mean()

    bullish = (
        (df["close"] > df["open"]) &
        (candle_body > average_body * 1.5)
    )

    bearish = (
        (df["close"] < df["open"]) &
        (candle_body > average_body * 1.5)
    )

    return bullish, bearish


def generate_signal(df):

    df = add_indicators(df)

    bullish_sweep, bearish_sweep = liquidity_sweep(df)
    bullish_structure, bearish_structure = market_structure(df)
    bullish_disp, bearish_disp = displacement(df)

    last = df.iloc[-1]

    long_score = 0
    short_score = 0

    # Liquidity
    if bullish_sweep.iloc[-1]:
        long_score += 25

    if bearish_sweep.iloc[-1]:
        short_score += 25

    # Market structure
    if bullish_structure.iloc[-1]:
        long_score += 20

    if bearish_structure.iloc[-1]:
        short_score += 20

    # EMA trend
    if last["ema20"] > last["ema50"]:
        long_score += 10

    if last["ema20"] < last["ema50"]:
        short_score += 10

    # Higher timeframe-style trend filter
    if last["close"] > last["ema200"]:
        long_score += 10

    if last["close"] < last["ema200"]:
        short_score += 10

    # Displacement
    if bullish_disp.iloc[-1]:
        long_score += 15

    if bearish_disp.iloc[-1]:
        short_score += 15

    # Volume
    if last["volume"] > last["volume_ma"]:
        if long_score > short_score:
            long_score += 10
        elif short_score > long_score:
            short_score += 10

    if long_score >= 70 and long_score > short_score:
        signal = "LONG"
        score = long_score

    elif short_score >= 70 and short_score > long_score:
        signal = "SHORT"
        score = short_score

    else:
        signal = "NO TRADE"
        score = max(long_score, short_score)

    return {
        "signal": signal,
        "score": int(score),
        "long_score": int(long_score),
        "short_score": int(short_score),
        "price": float(last["close"]),
        "atr": float(last["atr"])
    }

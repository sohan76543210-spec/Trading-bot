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


def detect_liquidity(df, lookback=20):
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


def detect_structure(df):
    previous_high = df["high"].shift(1)
    previous_low = df["low"].shift(1)

    bullish_bos = df["close"] > previous_high
    bearish_bos = df["close"] < previous_low

    return bullish_bos, bearish_bos


def detect_displacement(df):
    body = abs(df["close"] - df["open"])
    average_body = body.rolling(20).mean()

    bullish = (
        (df["close"] > df["open"]) &
        (body > average_body * 1.5)
    )

    bearish = (
        (df["close"] < df["open"]) &
        (body > average_body * 1.5)
    )

    return bullish, bearish


def detect_fvg(df):

    bullish_fvg = (
        df["low"] > df["high"].shift(2)
    )

    bearish_fvg = (
        df["high"] < df["low"].shift(2)
    )

    return bullish_fvg, bearish_fvg


def generate_signal(df):

    df = add_indicators(df)

    # Guard: EMA200/ATR/volume_ma need warm-up history. If the last row
    # still has NaNs (too little data was fetched), fail loudly instead of
    # silently comparing against NaN, which pandas treats as False for every
    # ">"/"<" check and would quietly bias the score toward "NO TRADE".
    required_cols = ["ema20", "ema50", "ema200", "atr", "volume_ma"]
    if df.iloc[-1][required_cols].isna().any():
        raise RuntimeError(
            "Not enough historical candles to compute indicators "
            "(ema200/atr/volume_ma still NaN on the latest row)."
        )

    bullish_sweep, bearish_sweep = detect_liquidity(df)
    bullish_bos, bearish_bos = detect_structure(df)
    bullish_disp, bearish_disp = detect_displacement(df)
    bullish_fvg, bearish_fvg = detect_fvg(df)

    last = df.iloc[-1]

    long_score = 0
    short_score = 0

    reasons_long = []
    reasons_short = []

    # -------------------------
    # LIQUIDITY
    # -------------------------

    if bullish_sweep.iloc[-1]:
        long_score += 25
        reasons_long.append("Bullish liquidity sweep")

    if bearish_sweep.iloc[-1]:
        short_score += 25
        reasons_short.append("Bearish liquidity sweep")

    # -------------------------
    # MARKET STRUCTURE
    # -------------------------

    if bullish_bos.iloc[-1]:
        long_score += 20
        reasons_long.append("Bullish structure break")

    if bearish_bos.iloc[-1]:
        short_score += 20
        reasons_short.append("Bearish structure break")

    # -------------------------
    # TREND
    # -------------------------

    if last["ema20"] > last["ema50"]:
        long_score += 10
        reasons_long.append("EMA bullish trend")

    if last["ema20"] < last["ema50"]:
        short_score += 10
        reasons_short.append("EMA bearish trend")

    # -------------------------
    # HTF STYLE FILTER
    # -------------------------

    if last["close"] > last["ema200"]:
        long_score += 10
        reasons_long.append("Above EMA200")

    if last["close"] < last["ema200"]:
        short_score += 10
        reasons_short.append("Below EMA200")

    # -------------------------
    # DISPLACEMENT
    # -------------------------

    if bullish_disp.iloc[-1]:
        long_score += 15
        reasons_long.append("Bullish displacement")

    if bearish_disp.iloc[-1]:
        short_score += 15
        reasons_short.append("Bearish displacement")

    # -------------------------
    # FVG
    # -------------------------

    if bullish_fvg.iloc[-1]:
        long_score += 10
        reasons_long.append("Bullish FVG")

    if bearish_fvg.iloc[-1]:
        short_score += 10
        reasons_short.append("Bearish FVG")

    # -------------------------
    # VOLUME
    # -------------------------

    if last["volume"] > last["volume_ma"]:

        if long_score > short_score:
            long_score += 10
            reasons_long.append("Volume confirmation")

        elif short_score > long_score:
            short_score += 10
            reasons_short.append("Volume confirmation")

    # -------------------------
    # FINAL DECISION
    # -------------------------

    if long_score >= 70 and long_score > short_score:

        signal = "LONG"
        score = long_score
        reasons = reasons_long

    elif short_score >= 70 and short_score > long_score:

        signal = "SHORT"
        score = short_score
        reasons = reasons_short

    else:

        signal = "NO TRADE"
        score = max(long_score, short_score)

        reasons = (
            reasons_long
            if long_score >= short_score
            else reasons_short
        )

    return {
        "signal": signal,
        "score": int(score),
        "long_score": int(long_score),
        "short_score": int(short_score),
        "price": float(last["close"]),
        "atr": float(last["atr"]),
        "reasons": reasons
    }

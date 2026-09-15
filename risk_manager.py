def calculate_trade(price, atr, direction):

    if direction == "LONG":
        stop_loss = price - atr * 1.5
        risk = price - stop_loss

        tp1 = price + risk * 2
        tp2 = price + risk * 3

    elif direction == "SHORT":
        stop_loss = price + atr * 1.5
        risk = stop_loss - price

        tp1 = price - risk * 2
        tp2 = price - risk * 3

    else:
        return None

    return {
        "entry": round(price, 2),
        "stop_loss": round(stop_loss, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "risk_reward_tp1": 2,
        "risk_reward_tp2": 3
    }

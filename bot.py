import os
import requests

from market_data import get_klines
from strategy import generate_signal
from risk_manager import calculate_trade


SYMBOL = "BTCUSDT"
INTERVAL = "15m"


def send_telegram(message):

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print(message)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message
        },
        timeout=20
    )


def main():

    df = get_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=500
    )

    result = generate_signal(df)

    print(result)

    if result["signal"] == "NO TRADE":

        message = (
            f"BTC/USDT\n\n"
            f"Signal: NO TRADE\n"
            f"Market Score: {result['score']}/100\n"
            f"Long Score: {result['long_score']}\n"
            f"Short Score: {result['short_score']}\n"
            f"Price: {result['price']}"
        )

        send_telegram(message)
        return

    trade = calculate_trade(
        result["price"],
        result["atr"],
        result["signal"]
    )

    message = (
        f"🚨 BTC/USDT SIGNAL\n\n"
        f"Direction: {result['signal']}\n"
        f"Score: {result['score']}/100\n\n"
        f"Entry: {trade['entry']}\n"
        f"Stop Loss: {trade['stop_loss']}\n"
        f"TP1: {trade['tp1']}\n"
        f"TP2: {trade['tp2']}\n\n"
        f"Risk/Reward:\n"
        f"TP1 = 1:{trade['risk_reward_tp1']}\n"
        f"TP2 = 1:{trade['risk_reward_tp2']}\n\n"
        f"Strategy: Liquidity + Market Structure + Momentum"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()

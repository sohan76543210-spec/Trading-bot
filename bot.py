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
        print("Telegram secrets are missing.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message
        },
        timeout=20
    )

    response.raise_for_status()


def main():

    df = get_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=300
    )

    result = generate_signal(df)

    print(result)

    signal = result["signal"]

    if signal == "NO TRADE":

        message = (
            "BTC/USDT\n\n"
            "Signal: NO TRADE\n"
            f"Score: {result['score']}/100\n"
            f"Long Score: {result['long_score']}\n"
            f"Short Score: {result['short_score']}\n"
            f"Price: {result['price']}\n\n"
            "Reasons:\n"
            + "\n".join(
                f"- {x}" for x in result["reasons"]
            )
        )

        send_telegram(message)
        return

    trade = calculate_trade(
        result["price"],
        result["atr"],
        signal
    )

    message = (
        "🚨 BTC/USDT SIGNAL\n\n"
        f"Direction: {signal}\n"
        f"Score: {result['score']}/100\n\n"
        f"Entry: {trade['entry']}\n"
        f"Stop Loss: {trade['stop_loss']}\n"
        f"TP1: {trade['tp1']}\n"
        f"TP2: {trade['tp2']}\n\n"
        "Reasons:\n"
        + "\n".join(
            f"- {x}" for x in result["reasons"]
        )
    )

    send_telegram(message)


if __name__ == "__main__":
    main()


            timeout=20
        )

        if not response.ok:
            print("Telegram API Error:")
            print(response.status_code)
            print(response.text)
            return False

        print("Telegram message sent successfully.")
        return True

    except requests.RequestException as e:
        print("Telegram connection error:")
        print(e)
        return False


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

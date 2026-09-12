import requests

BASE_URL = "https://fapi.binance.com"


def get_price(symbol):
    url = f"{BASE_URL}/fapi/v1/ticker/24hr?symbol={symbol}"
    
    response = requests.get(url)
    data = response.json()

    return {
        "symbol": symbol,
        "price": float(data["lastPrice"]),
        "change_24h": float(data["priceChangePercent"]),
        "volume": float(data["quoteVolume"])
    }


def get_all_prices(coins):
    results = []

    for coin in coins:
        try:
            data = get_price(coin)
            results.append(data)

        except Exception:
            pass

    return results

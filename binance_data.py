import requests
import time
from datetime import datetime, timezone

BASE_URL = "https://www.okx.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_okx_swaps():
    url = f"{BASE_URL}/api/v5/public/instruments"
    params = {"instType": "SWAP"}

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    if data.get("code") != "0":
        return set()

    return {
        item["instId"]
        for item in data["data"]
        if item.get("state") == "live"
        and item.get("instId", "").endswith("-USDT-SWAP")
    }


def to_okx_symbol(symbol):
    # BTCUSDT -> BTC-USDT-SWAP
    if symbol.endswith("USDT"):
        base = symbol[:-4]
        return f"{base}-USDT-SWAP"

    return None


def get_daily_candles(inst_id, limit=300):
    url = f"{BASE_URL}/api/v5/market/candles"

    params = {
        "instId": inst_id,
        "bar": "1Dutc",
        "limit": str(limit)
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    if data.get("code") != "0":
        return []

    candles = []

    for row in data.get("data", []):
        candles.append({
            "ts": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[7]) if len(row) > 7 else 0.0,
            "confirm": row[8] if len(row) > 8 else "0"
        })

    # OKX en yeni mumu önce döndürüyor.
    # Hesaplarda eskiden yeniye kullanacağız.
    candles.sort(key=lambda x: x["ts"])

    return candles


def aggregate_period(candles, period):
    if not candles:
        return None

    now = datetime.now(timezone.utc)

    selected = []

    for candle in candles:
        dt = datetime.fromtimestamp(
            candle["ts"] / 1000,
            tz=timezone.utc
        )

        if period == "day":
            match = (
                dt.year == now.year
                and dt.month == now.month
                and dt.day == now.day
            )

        elif period == "week":
            now_iso = now.isocalendar()
            dt_iso = dt.isocalendar()

            match = (
                dt_iso.year == now_iso.year
                and dt_iso.week == now_iso.week
            )

        elif period == "month":
            match = (
                dt.year == now.year
                and dt.month == now.month
            )

        elif period == "year":
            match = dt.year == now.year

        else:
            match = False

        if match:
            selected.append(candle)

    if not selected:
        return None

    return {
        "open": selected[0]["open"],
        "high": max(x["high"] for x in selected),
        "low": min(x["low"] for x in selected),
        "close": selected[-1]["close"]
    }


def location_percent(price, high, low):
    if high == low:
        return 50.0

    return ((price - low) / (high - low)) * 100


def percent_distance(price, level):
    if level == 0:
        return 0.0

    return ((price - level) / level) * 100


def analyze_coin(symbol, available_swaps):
    inst_id = to_okx_symbol(symbol)

    if not inst_id or inst_id not in available_swaps:
        return None

    candles = get_daily_candles(inst_id)

    if len(candles) < 2:
        return None

    price = candles[-1]["close"]

    day = aggregate_period(candles, "day")
    week = aggregate_period(candles, "week")
    month = aggregate_period(candles, "month")
    year = aggregate_period(candles, "year")

    if not all([day, week, month, year]):
        return None

    # Son 5 günlük mum rengi
    last_5 = candles[-5:]

    colors = "".join(
        "🟢" if c["close"] >= c["open"] else "🔴"
        for c in last_5
    )

    # Bugünkü hacim
    today_volume = candles[-1]["volume"]

    # Önceki tamamlanmış 14 günlük ortalama hacim
    previous_14 = candles[-15:-1]

    avg_14_volume = (
        sum(c["volume"] for c in previous_14) / len(previous_14)
        if previous_14
        else 0
    )

    volume_vs_14 = (
        ((today_volume - avg_14_volume) / avg_14_volume) * 100
        if avg_14_volume > 0
        else 0
    )

    # Günlük ve haftalık değişim:
    # anlık fiyatın dönem açılışına göre yüzdesi
    daily_change = percent_distance(price, day["open"])
    weekly_change = percent_distance(price, week["open"])

    return {
        "Coin": symbol.replace("USDT", ""),
        "OKX": inst_id,
        "Fiyat": price,

        "Gün %": daily_change,
        "Hafta %": weekly_change,

        "Gün Açılış": day["open"],
        "Gün Durum": "ÜSTÜ" if price >= day["open"] else "ALTI",

        "Gün O": day["open"],
        "Gün H": day["high"],
        "Gün L": day["low"],
        "Gün C": day["close"],

        "Hafta O": week["open"],
        "Hafta H": week["high"],
        "Hafta L": week["low"],
        "Hafta C": week["close"],

        "Ay O": month["open"],
        "Ay H": month["high"],
        "Ay L": month["low"],
        "Ay C": month["close"],

        "Yıl O": year["open"],
        "Yıl H": year["high"],
        "Yıl L": year["low"],
        "Yıl C": year["close"],

        "Gün Konum %": location_percent(
            price, day["high"], day["low"]
        ),

        "Hafta Konum %": location_percent(
            price, week["high"], week["low"]
        ),

        "Ay Konum %": location_percent(
            price, month["high"], month["low"]
        ),

        "Yıl Konum %": location_percent(
            price, year["high"], year["low"]
        ),

        "Gün H Uzaklık %": percent_distance(
            price, day["high"]
        ),

        "Gün L Uzaklık %": percent_distance(
            price, day["low"]
        ),

        "Son 5 Gün": colors,

        "Gün Hacim USDT": today_volume,
        "14G Ort Hacim": avg_14_volume,
        "14G Hacim Fark %": volume_vs_14
    }


def get_scanner_data(coins):
    available_swaps = get_okx_swaps()

    results = []

    for symbol in coins:
        try:
            result = analyze_coin(
                symbol,
                available_swaps
            )

            if result:
                results.append(result)

            # API'yi gereksiz zorlamamak için küçük ara
            time.sleep(0.06)

        except Exception as e:
            print(f"{symbol}: {e}")

    return results

import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE_URL = "https://www.okx.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ---------------------------------------------------------
# OKX ISTEK MOTORU
# ---------------------------------------------------------

def okx_get(path, params=None):
    url = BASE_URL + path

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=(5, 12)
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "0":
        raise RuntimeError(
            f"OKX hata kodu: {data.get('code')} - "
            f"{data.get('msg')}"
        )

    return data.get("data", [])


# ---------------------------------------------------------
# BINANCE SEMBOLÜ -> OKX SEMBOLÜ
# BTCUSDT -> BTC-USDT-SWAP
# ---------------------------------------------------------

def to_okx_symbol(symbol):
    if not symbol.endswith("USDT"):
        return None

    base = symbol[:-4]

    return f"{base}-USDT-SWAP"


# ---------------------------------------------------------
# TÜM OKX USDT SWAP FİYATLARI
# Tek API isteği
# ---------------------------------------------------------

def get_all_tickers():
    rows = okx_get(
        "/api/v5/market/tickers",
        {"instType": "SWAP"}
    )

    result = {}

    for row in rows:
        inst_id = row.get("instId", "")

        if not inst_id.endswith("-USDT-SWAP"):
            continue

        try:
            result[inst_id] = float(row["last"])
        except (ValueError, TypeError, KeyError):
            continue

    return result


# ---------------------------------------------------------
# MUM VERİSİ
# ---------------------------------------------------------

def get_candles(inst_id, bar, limit):
    rows = okx_get(
        "/api/v5/market/candles",
        {
            "instId": inst_id,
            "bar": bar,
            "limit": str(limit)
        }
    )

    candles = []

    for row in rows:
        try:
            candles.append({
                "ts": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),

                # OKX quote currency volume
                # USDT swap için yaklaşık USDT hacmi
                "volume": float(row[7]),

                # 1 = kapanmış mum
                # 0 = halen açık mum
                "confirm": str(row[8])
            })

        except (ValueError, TypeError, IndexError):
            continue

    # OKX yeniyi önce gönderiyor.
    # Hesaplama için eskiden yeniye çeviriyoruz.
    candles.sort(
        key=lambda x: x["ts"]
    )

    return candles


# ---------------------------------------------------------
# DÖNEM OHLC
# ---------------------------------------------------------

def period_ohlc(candles, period):
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

            a = dt.isocalendar()
            b = now.isocalendar()

            match = (
                a.year == b.year
                and a.week == b.week
            )

        elif period == "month":

            match = (
                dt.year == now.year
                and dt.month == now.month
            )

        elif period == "year":

            match = (
                dt.year == now.year
            )

        else:
            match = False

        if match:
            selected.append(candle)

    if not selected:
        return None

    return {
        "open": selected[0]["open"],

        "high": max(
            x["high"]
            for x in selected
        ),

        "low": min(
            x["low"]
            for x in selected
        ),

        "close": selected[-1]["close"]
    }


# ---------------------------------------------------------
# YÜZDE HESAPLARI
# ---------------------------------------------------------

def change_percent(price, base):
    if base == 0:
        return 0.0

    return (
        (price - base)
        / base
        * 100
    )


def location_percent(price, high, low):
    if high == low:
        return 50.0

    value = (
        (price - low)
        / (high - low)
        * 100
    )

    # Anlık sapmalarda tablo 0-100 dışına taşmasın
    return max(
        0.0,
        min(100.0, value)
    )


def distance_percent(price, level):
    if price == 0:
        return 0.0

    return (
        abs(level - price)
        / price
        * 100
    )


# ---------------------------------------------------------
# TEK COIN ANALİZİ
# ---------------------------------------------------------

def analyze_coin(symbol, ticker_map):

    inst_id = to_okx_symbol(symbol)

    if not inst_id:
        return None

    # OKX'te olmayan Binance coinlerini otomatik atla
    if inst_id not in ticker_map:
        return None

    price = ticker_map[inst_id]

    # Gün / hafta / ay + son 5 gün + hacim için
    # 40 günlük veri yeterli
    daily = get_candles(
        inst_id,
        "1Dutc",
        40
    )

    # Yıllık OHLC için aylık mumları kullanıyoruz.
    # Böylece yıl sonunda 300 günlük veri sınırı sorunu olmaz.
    monthly = get_candles(
        inst_id,
        "1Mutc",
        12
    )

    if not daily or not monthly:
        return None

    day = period_ohlc(
        daily,
        "day"
    )

    week = period_ohlc(
        daily,
        "week"
    )

    month = period_ohlc(
        daily,
        "month"
    )

    year = period_ohlc(
        monthly,
        "year"
    )

    if not all([
        day,
        week,
        month,
        year
    ]):
        return None


    # -----------------------------------------------------
    # SON 5 TAMAMLANMIŞ GÜNLÜK MUM
    # -----------------------------------------------------

    completed = [
        candle
        for candle in daily
        if candle["confirm"] == "1"
    ]

    last_5 = completed[-5:]

    colors = "".join(
        "🟢"
        if c["close"] >= c["open"]
        else "🔴"
        for c in last_5
    )


    # -----------------------------------------------------
    # HACİM
    # -----------------------------------------------------

    current_daily = daily[-1]

    today_volume = current_daily[
        "volume"
    ]

    previous_14 = completed[-14:]

    if previous_14:

        avg_14_volume = (
            sum(
                c["volume"]
                for c in previous_14
            )
            / len(previous_14)
        )

    else:
        avg_14_volume = 0.0


    if avg_14_volume > 0:

        volume_vs_14 = (
            (today_volume - avg_14_volume)
            / avg_14_volume
            * 100
        )

    else:
        volume_vs_14 = 0.0


    # -----------------------------------------------------
    # ANA SONUÇ
    # -----------------------------------------------------

    return {

        "Coin": symbol.replace(
            "USDT",
            ""
        ),

        "Fiyat": price,

        "Gün %": change_percent(
            price,
            day["open"]
        ),

        "Hafta %": change_percent(
            price,
            week["open"]
        ),

        "Gün Durum": (
            "ÜSTÜ"
            if price >= day["open"]
            else "ALTI"
        ),

        # ---------- GÜN ----------

        "Gün O": day["open"],
        "Gün H": day["high"],
        "Gün L": day["low"],
        "Gün C": day["close"],

        "Gün Konum %": location_percent(
            price,
            day["high"],
            day["low"]
        ),

        # ---------- HAFTA ----------

        "Hafta O": week["open"],
        "Hafta H": week["high"],
        "Hafta L": week["low"],
        "Hafta C": week["close"],

        "Hafta Konum %": location_percent(
            price,
            week["high"],
            week["low"]
        ),

        # ---------- AY ----------

        "Ay O": month["open"],
        "Ay H": month["high"],
        "Ay L": month["low"],
        "Ay C": month["close"],

        "Ay Konum %": location_percent(
            price,
            month["high"],
            month["low"]
        ),

        # ---------- YIL ----------

        "Yıl O": year["open"],
        "Yıl H": year["high"],
        "Yıl L": year["low"],
        "Yıl C": year["close"],

        "Yıl Konum %": location_percent(
            price,
            year["high"],
            year["low"]
        ),

        # ---------- UZAKLIK ----------

        "Gün H Uzaklık %": distance_percent(
            price,
            day["high"]
        ),

        "Gün L Uzaklık %": distance_percent(
            price,
            day["low"]
        ),

        # ---------- MOMENTUM ----------

        "Son 5 Gün": colors,

        # ---------- HACİM ----------

        "Gün Hacim USDT": today_volume,

        "14G Ort Hacim": avg_14_volume,

        "14G Hacim Fark %": volume_vs_14
    }


# ---------------------------------------------------------
# TÜM TARAYICI
# ---------------------------------------------------------

def get_scanner_data(coins):

    # Bütün anlık fiyatları yalnızca 1 istekte al
    ticker_map = get_all_tickers()

    results = []

    # OKX limitlerini zorlamamak için 2 paralel işçi.
    # Her coin 2 mum isteği yapıyor.
    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        futures = {
            executor.submit(
                analyze_coin,
                symbol,
                ticker_map
            ): symbol

            for symbol in coins
        }

        for future in as_completed(
            futures
        ):

            symbol = futures[future]

            try:
                result = future.result()

                if result:
                    results.append(
                        result
                    )

            except Exception as e:

                print(
                    f"{symbol} hata: {e}"
                )

    return results

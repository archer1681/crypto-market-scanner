import requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache


BASE_URL = "https://www.okx.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================================================
# OKX İSTEK MOTORU
# =========================================================

def okx_get(path, params=None):
    response = requests.get(
        BASE_URL + path,
        params=params,
        headers=HEADERS,
        timeout=(5, 12)
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("code") != "0":
        raise RuntimeError(
            f"OKX hata: {payload.get('code')} - "
            f"{payload.get('msg')}"
        )

    return payload.get("data", [])


# =========================================================
# BTCUSDT -> BTC-USDT-SWAP
# =========================================================

def to_okx_symbol(symbol):
    if not symbol.endswith("USDT"):
        return None

    return f"{symbol[:-4]}-USDT-SWAP"


# =========================================================
# TÜM ANLIK FİYATLAR
# TEK API İSTEĞİ
# =========================================================

def get_all_tickers():
    rows = okx_get(
        "/api/v5/market/tickers",
        {"instType": "SWAP"}
    )

    prices = {}

    for row in rows:
        inst_id = row.get("instId", "")

        if not inst_id.endswith("-USDT-SWAP"):
            continue

        try:
            prices[inst_id] = float(row["last"])
        except Exception:
            pass

    return prices


# =========================================================
# MUM VERİSİ
# =========================================================

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
                "volume": float(row[7]),
                "confirm": str(row[8])
            })
        except Exception:
            continue

    candles.sort(key=lambda x: x["ts"])

    return candles


# =========================================================
# TÜRKİYE 03:00 = YENİ KRİPTO GÜNÜ
#
# Bu anahtar yalnızca 03:00'te değişir.
# Geçmiş veri önbelleğinin yenilenmesini sağlar.
# =========================================================

def market_day_key():
    now_utc = datetime.now(timezone.utc)

    # Türkiye 03:00 = UTC 00:00
    return now_utc.date().isoformat()


# =========================================================
# TARİH YARDIMCISI
# =========================================================

def candle_datetime(candle):
    return datetime.fromtimestamp(
        candle["ts"] / 1000,
        tz=timezone.utc
    )


# =========================================================
# OHLC BİRLEŞTİRME
# =========================================================

def combine_ohlc(candles, current_price=None):
    if not candles:
        return None

    candles = sorted(
        candles,
        key=lambda x: x["ts"]
    )

    result = {
        "open": candles[0]["open"],
        "high": max(x["high"] for x in candles),
        "low": min(x["low"] for x in candles),
        "close": candles[-1]["close"]
    }

    if current_price is not None:
        result["close"] = current_price

    return result


# =========================================================
# DEĞİŞMEYEN GEÇMİŞ VERİ
#
# Bir coin için bu bölüm aynı kripto günü içerisinde
# yalnızca 1 kez indirilir.
# =========================================================

def build_coin_history(symbol):
    inst_id = to_okx_symbol(symbol)

    if not inst_id:
        return None

    daily = get_candles(
        inst_id,
        "1Dutc",
        40
    )

    monthly = get_candles(
        inst_id,
        "1Mutc",
        12
    )

    # Sadece kapanmış mumlar
    completed_daily = [
        c for c in daily
        if c["confirm"] == "1"
    ]

    completed_monthly = [
        c for c in monthly
        if c["confirm"] == "1"
    ]

    if len(completed_daily) < 14:
        return None

    # Son 5 tamamlanmış günlük mum
    last_5 = completed_daily[-5:]

    colors = "".join(
        "🟢" if c["close"] >= c["open"] else "🔴"
        for c in last_5
    )

    # Son 14 tamamlanmış gün hacim ortalaması
    last_14 = completed_daily[-14:]

    avg_14_volume = (
        sum(c["volume"] for c in last_14)
        / len(last_14)
    )

    return {
        "inst_id": inst_id,
        "daily": completed_daily,
        "monthly": completed_monthly,
        "last_5": colors,
        "avg_14_volume": avg_14_volume
    }


# =========================================================
# GÜNLÜK GEÇMİŞ CACHE
#
# day_key değişmediği sürece tekrar çalışmaz.
# =========================================================

@lru_cache(maxsize=8)
def get_history_snapshot(coins_tuple, day_key):
    results = {}

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        futures = {
            executor.submit(
                build_coin_history,
                symbol
            ): symbol

            for symbol in coins_tuple
        }

        for future in as_completed(futures):
            symbol = futures[future]

            try:
                result = future.result()

                if result:
                    results[symbol] = result

            except Exception as e:
                print(
                    f"Geçmiş veri {symbol}: {e}"
                )

    return results


# =========================================================
# BUGÜNKÜ CANLI MUM
#
# Gün içinde değişen esas OHLC bilgisi budur.
# =========================================================

def get_live_day(inst_id):
    candles = get_candles(
        inst_id,
        "1Dutc",
        1
    )

    if not candles:
        return None

    return candles[-1]


# =========================================================
# YÜZDE HESAPLARI
# =========================================================

def change_percent(price, base):
    if not base:
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

    return max(
        0.0,
        min(100.0, value)
    )


def distance_percent(price, level):
    if not price:
        return 0.0

    return (
        abs(level - price)
        / price
        * 100
    )


# =========================================================
# TEK COIN HESAPLAMA
# =========================================================

def calculate_coin(
    symbol,
    history,
    live_day,
    price
):

    if not history or not live_day:
        return None

    now = datetime.now(timezone.utc)

    completed_daily = history["daily"]
    completed_monthly = history["monthly"]


    # -----------------------------------------------------
    # GÜN
    # -----------------------------------------------------

    day = {
        "open": live_day["open"],
        "high": live_day["high"],
        "low": live_day["low"],
        "close": price
    }


    # -----------------------------------------------------
    # HAFTA
    # -----------------------------------------------------

    now_iso = now.isocalendar()

    week_candles = []

    for candle in completed_daily:
        dt = candle_datetime(candle)
        iso = dt.isocalendar()

        if (
            iso.year == now_iso.year
            and iso.week == now_iso.week
        ):
            week_candles.append(candle)

    week_candles.append(live_day)

    week = combine_ohlc(
        week_candles,
        price
    )


    # -----------------------------------------------------
    # AY
    # -----------------------------------------------------

    month_candles = []

    for candle in completed_daily:
        dt = candle_datetime(candle)

        if (
            dt.year == now.year
            and dt.month == now.month
        ):
            month_candles.append(candle)

    month_candles.append(live_day)

    month = combine_ohlc(
        month_candles,
        price
    )


    # -----------------------------------------------------
    # YIL
    #
    # Önce tamamlanmış aylık mumlar,
    # sonra mevcut ayın canlı OHLC'si.
    # -----------------------------------------------------

    year_parts = []

    for candle in completed_monthly:
        dt = candle_datetime(candle)

        if dt.year == now.year:
            year_parts.append(candle)

    # Mevcut ayı sentetik mum olarak ekle
    current_month_candle = {
        "ts": live_day["ts"],
        "open": month["open"],
        "high": month["high"],
        "low": month["low"],
        "close": price,
        "volume": 0,
        "confirm": "0"
    }

    year_parts.append(
        current_month_candle
    )

    year = combine_ohlc(
        year_parts,
        price
    )


    # -----------------------------------------------------
    # HACİM
    # -----------------------------------------------------

    today_volume = live_day["volume"]

    avg_14_volume = history[
        "avg_14_volume"
    ]

    if avg_14_volume > 0:
        volume_vs_14 = (
            (today_volume - avg_14_volume)
            / avg_14_volume
            * 100
        )
    else:
        volume_vs_14 = 0.0


    # -----------------------------------------------------
    # SONUÇ
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

        # GÜN
        "Gün O": day["open"],
        "Gün H": day["high"],
        "Gün L": day["low"],
        "Gün C": price,

        "Gün Konum %": location_percent(
            price,
            day["high"],
            day["low"]
        ),

        # HAFTA
        "Hafta O": week["open"],
        "Hafta H": week["high"],
        "Hafta L": week["low"],
        "Hafta C": price,

        "Hafta Konum %": location_percent(
            price,
            week["high"],
            week["low"]
        ),

        # AY
        "Ay O": month["open"],
        "Ay H": month["high"],
        "Ay L": month["low"],
        "Ay C": price,

        "Ay Konum %": location_percent(
            price,
            month["high"],
            month["low"]
        ),

        # YIL
        "Yıl O": year["open"],
        "Yıl H": year["high"],
        "Yıl L": year["low"],
        "Yıl C": price,

        "Yıl Konum %": location_percent(
            price,
            year["high"],
            year["low"]
        ),

        # UZAKLIK
        "Gün H Uzaklık %": distance_percent(
            price,
            day["high"]
        ),

        "Gün L Uzaklık %": distance_percent(
            price,
            day["low"]
        ),

        # SON 5 KAPANMIŞ MUM
        "Son 5 Gün": history[
            "last_5"
        ],

        # HACİM
        "Gün Hacim USDT": today_volume,

        "14G Ort Hacim": avg_14_volume,

        "14G Hacim Fark %": volume_vs_14
    }


# =========================================================
# ANA TARAYICI
# =========================================================

def get_scanner_data(coins):

    coins_tuple = tuple(coins)

    # 03:00'te değişen günlük cache anahtarı
    day_key = market_day_key()

    # Geçmiş veri aynı gün içinde cache'den gelir.
    history_map = get_history_snapshot(
        coins_tuple,
        day_key
    )

    # Bütün anlık fiyatlar yalnızca 1 API isteği
    ticker_map = get_all_tickers()

    results = []


    # -----------------------------------------------------
    # Sadece bugünkü günlük mumları yenile
    # -----------------------------------------------------

    live_days = {}

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        futures = {}

        for symbol in coins:

            history = history_map.get(
                symbol
            )

            if not history:
                continue

            inst_id = history[
                "inst_id"
            ]

            # OKX'te hâlâ mevcut mu?
            if inst_id not in ticker_map:
                continue

            futures[
                executor.submit(
                    get_live_day,
                    inst_id
                )
            ] = symbol


        for future in as_completed(
            futures
        ):

            symbol = futures[future]

            try:
                live_day = future.result()

                if live_day:
                    live_days[
                        symbol
                    ] = live_day

            except Exception as e:
                print(
                    f"Canlı mum {symbol}: {e}"
                )


    # -----------------------------------------------------
    # API YOK: sadece yerel hesaplama
    # -----------------------------------------------------

    for symbol in coins:

        history = history_map.get(
            symbol
        )

        live_day = live_days.get(
            symbol
        )

        if not history or not live_day:
            continue

        inst_id = history[
            "inst_id"
        ]

        price = ticker_map.get(
            inst_id
        )

        if price is None:
            continue

        result = calculate_coin(
            symbol,
            history,
            live_day,
            price
        )

        if result:
            results.append(result)

    return results

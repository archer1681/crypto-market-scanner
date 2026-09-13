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

    candles.sort(
        key=lambda x: x["ts"]
    )

    return candles


# =========================================================
# TÜRKİYE 03:00 = YENİ KRİPTO GÜNÜ
# =========================================================

def market_day_key():
    now_utc = datetime.now(
        timezone.utc
    )

    return now_utc.date().isoformat()


# =========================================================
# SAATLİK CACHE ANAHTARI
# =========================================================

def market_hour_key():
    now = datetime.now(
        timezone.utc
    )

    return now.strftime(
        "%Y-%m-%d-%H"
    )


# =========================================================
# 4 SAATLİK CACHE ANAHTARI
# =========================================================

def market_4h_key():
    now = datetime.now(
        timezone.utc
    )

    block = now.hour // 4

    return (
        f"{now.date().isoformat()}-"
        f"{block}"
    )


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

def combine_ohlc(
    candles,
    current_price=None
):
    if not candles:
        return None

    candles = sorted(
        candles,
        key=lambda x: x["ts"]
    )

    result = {
        "open": candles[0]["open"],
        "high": max(
            x["high"]
            for x in candles
        ),
        "low": min(
            x["low"]
            for x in candles
        ),
        "close": candles[-1]["close"]
    }

    if current_price is not None:
        result["close"] = current_price

    return result


# =========================================================
# DEĞİŞMEYEN GEÇMİŞ VERİ
# =========================================================

def build_coin_history(symbol):
    inst_id = to_okx_symbol(
        symbol
    )

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

    completed_daily = [
        c
        for c in daily
        if c["confirm"] == "1"
    ]

    completed_monthly = [
        c
        for c in monthly
        if c["confirm"] == "1"
    ]

    if len(
        completed_daily
    ) < 14:
        return None

    last_5 = (
        completed_daily[-5:]
    )

    colors = "".join(
        (
            "🟢"
            if c["close"] >= c["open"]
            else "🔴"
        )
        for c in last_5
    )

    last_14 = (
        completed_daily[-14:]
    )

    avg_14_volume = (
        sum(
            c["volume"]
            for c in last_14
        )
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
# =========================================================

@lru_cache(maxsize=8)
def get_history_snapshot(
    coins_tuple,
    day_key
):
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

        for future in as_completed(
            futures
        ):
            symbol = futures[
                future
            ]

            try:
                result = (
                    future.result()
                )

                if result:
                    results[
                        symbol
                    ] = result

            except Exception as e:
                print(
                    f"Geçmiş veri "
                    f"{symbol}: {e}"
                )

    return results


# =========================================================
# BUGÜNKÜ CANLI MUM
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

def change_percent(
    price,
    base
):
    if not base:
        return 0.0

    return (
        (price - base)
        / base
        * 100
    )


def location_percent(
    price,
    high,
    low
):
    if high == low:
        return 50.0

    value = (
        (price - low)
        / (high - low)
        * 100
    )

    return max(
        0.0,
        min(
            100.0,
            value
        )
    )


def distance_percent(
    price,
    level
):
    if not price:
        return 0.0

    return (
        abs(
            level - price
        )
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

    if (
        not history
        or not live_day
    ):
        return None

    now = datetime.now(
        timezone.utc
    )

    completed_daily = (
        history["daily"]
    )

    completed_monthly = (
        history["monthly"]
    )


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

    now_iso = (
        now.isocalendar()
    )

    week_candles = []

    for candle in completed_daily:
        dt = candle_datetime(
            candle
        )

        iso = dt.isocalendar()

        if (
            iso.year
            == now_iso.year
            and iso.week
            == now_iso.week
        ):
            week_candles.append(
                candle
            )

    week_candles.append(
        live_day
    )

    week = combine_ohlc(
        week_candles,
        price
    )


    # -----------------------------------------------------
    # AY
    # -----------------------------------------------------

    month_candles = []

    for candle in completed_daily:
        dt = candle_datetime(
            candle
        )

        if (
            dt.year
            == now.year
            and dt.month
            == now.month
        ):
            month_candles.append(
                candle
            )

    month_candles.append(
        live_day
    )

    month = combine_ohlc(
        month_candles,
        price
    )


    # -----------------------------------------------------
    # YIL
    # -----------------------------------------------------

    year_parts = []

    for candle in completed_monthly:
        dt = candle_datetime(
            candle
        )

        if (
            dt.year
            == now.year
        ):
            year_parts.append(
                candle
            )

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

    today_volume = (
        live_day["volume"]
    )

    avg_14_volume = history[
        "avg_14_volume"
    ]

    if avg_14_volume > 0:

        volume_vs_14 = (
            (
                today_volume
                - avg_14_volume
            )
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

        "Gün O": day["open"],
        "Gün H": day["high"],
        "Gün L": day["low"],
        "Gün C": price,

        "Gün Konum %": location_percent(
            price,
            day["high"],
            day["low"]
        ),

        "Hafta O": week["open"],
        "Hafta H": week["high"],
        "Hafta L": week["low"],
        "Hafta C": price,

        "Hafta Konum %":
            location_percent(
                price,
                week["high"],
                week["low"]
            ),

        "Ay O": month["open"],
        "Ay H": month["high"],
        "Ay L": month["low"],
        "Ay C": price,

        "Ay Konum %":
            location_percent(
                price,
                month["high"],
                month["low"]
            ),

        "Yıl O": year["open"],
        "Yıl H": year["high"],
        "Yıl L": year["low"],
        "Yıl C": price,

        "Yıl Konum %":
            location_percent(
                price,
                year["high"],
                year["low"]
            ),

        "Gün H Uzaklık %":
            distance_percent(
                price,
                day["high"]
            ),

        "Gün L Uzaklık %":
            distance_percent(
                price,
                day["low"]
            ),

        "Son 5 Gün":
            history["last_5"],

        "Gün Hacim USDT":
            today_volume,

        "14G Ort Hacim":
            avg_14_volume,

        "14G Hacim Fark %":
            volume_vs_14
    }


# =========================================================
# ANA TARAYICI
# =========================================================

def get_scanner_data(coins):

    coins_tuple = tuple(
        coins
    )

    day_key = (
        market_day_key()
    )

    history_map = (
        get_history_snapshot(
            coins_tuple,
            day_key
        )
    )

    ticker_map = (
        get_all_tickers()
    )

    results = []

    live_days = {}


    # -----------------------------------------------------
    # BUGÜNKÜ GÜNLÜK MUMLAR
    # -----------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        futures = {}

        for symbol in coins:

            history = (
                history_map.get(
                    symbol
                )
            )

            if not history:
                continue

            inst_id = history[
                "inst_id"
            ]

            if (
                inst_id
                not in ticker_map
            ):
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

            symbol = futures[
                future
            ]

            try:
                live_day = (
                    future.result()
                )

                if live_day:
                    live_days[
                        symbol
                    ] = live_day

            except Exception as e:
                print(
                    f"Canlı mum "
                    f"{symbol}: {e}"
                )


    # -----------------------------------------------------
    # YEREL HESAPLAMA
    # -----------------------------------------------------

    for symbol in coins:

        history = (
            history_map.get(
                symbol
            )
        )

        live_day = (
            live_days.get(
                symbol
            )
        )

        if (
            not history
            or not live_day
        ):
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
            results.append(
                result
            )

    return results


# =========================================================
# =========================================================
# MUM AKIŞI / TREND YAPISI MOTORU
# =========================================================
# =========================================================


# =========================================================
# MUM YÖNÜ
#
# Yaklaşık %0.05 ve daha küçük gövdeler DOJI
# =========================================================

DOJI_LIMIT_PERCENT = 0.05


def candle_direction(candle):

    open_price = candle[
        "open"
    ]

    close_price = candle[
        "close"
    ]

    if not open_price:
        return "doji"

    body_percent = (
        abs(
            close_price
            - open_price
        )
        / open_price
        * 100
    )

    if (
        body_percent
        <= DOJI_LIMIT_PERCENT
    ):
        return "doji"

    if (
        close_price
        > open_price
    ):
        return "up"

    return "down"


# =========================================================
# HAFTA ANAHTARI
# =========================================================

def week_key(candle):

    dt = candle_datetime(
        candle
    )

    iso = dt.isocalendar()

    return (
        iso.year,
        iso.week
    )


# =========================================================
# AY ANAHTARI
# =========================================================

def month_key(candle):

    dt = candle_datetime(
        candle
    )

    return (
        dt.year,
        dt.month
    )


# =========================================================
# GÜNLÜK MUMLARDAN HAFTALIK MUM ÜRET
#
# Yalnızca tamamlanmış haftalar.
# =========================================================

def build_completed_weeks(
    completed_daily
):

    groups = {}

    for candle in completed_daily:

        key = week_key(
            candle
        )

        groups.setdefault(
            key,
            []
        ).append(
            candle
        )


    now = datetime.now(
        timezone.utc
    )

    current_iso = (
        now.isocalendar()
    )

    current_key = (
        current_iso.year,
        current_iso.week
    )


    weeks = []

    for key in sorted(
        groups.keys()
    ):

        # Devam eden hafta kullanılmaz
        if key == current_key:
            continue

        candles = sorted(
            groups[key],
            key=lambda x: x["ts"]
        )

        if not candles:
            continue

        weeks.append({
            "ts": candles[0]["ts"],

            "open":
                candles[0]["open"],

            "high":
                max(
                    c["high"]
                    for c in candles
                ),

            "low":
                min(
                    c["low"]
                    for c in candles
                ),

            "close":
                candles[-1]["close"],

            # Hangi ayda kapandı?
            "close_ts":
                candles[-1]["ts"]
        })


    return weeks


# =========================================================
# AYLIK AÇILIŞ HARİTASI
#
# Günlük mumlardan oluşturulur.
# Böylece son haftaların ilgili ay açılışı bulunur.
# =========================================================

def build_month_open_map(
    completed_daily
):

    result = {}

    candles = sorted(
        completed_daily,
        key=lambda x: x["ts"]
    )

    for candle in candles:

        key = month_key(
            candle
        )

        if key not in result:

            result[key] = (
                candle["open"]
            )

   
    return result


# =========================================================
# HAFTALIK AÇILIŞ HARİTASI
#
# Her günlük mumun ait olduğu haftanın ilk açılışını tutar.
# =========================================================

def build_week_open_map(
    completed_daily
):

    result = {}

    candles = sorted(
        completed_daily,
        key=lambda x: x["ts"]
    )

    for candle in candles:

        key = week_key(
            candle
        )

        if key not in result:

            result[key] = (
                candle["open"]
            )

    return result


# =========================================================
# HAFTALIK 4 KUTU
#
# İç renk:
# Haftalık mum yönü
#
# Arka plan:
# Haftalık kapanış ilgili aylık açılışın
# altındaysa MOR
# =========================================================

def make_weekly_flow(
    completed_daily
):

    weeks = build_completed_weeks(
        completed_daily
    )

    month_open_map = (
        build_month_open_map(
            completed_daily
        )
    )

    result = []

    for candle in weeks[-4:]:

        close_dt = datetime.fromtimestamp(
            candle["close_ts"] / 1000,
            tz=timezone.utc
        )

        m_key = (
            close_dt.year,
            close_dt.month
        )

        monthly_open = (
            month_open_map.get(
                m_key
            )
        )

        below_parent_open = False

        if monthly_open is not None:

            below_parent_open = (
                candle["close"]
                < monthly_open
            )

        result.append({
            "direction": candle_direction(
                candle
            ),

            "below_parent_open":
                below_parent_open
        })

    return result


# =========================================================
# GÜNLÜK 7 KUTU
#
# İç renk:
# Günlük mum yönü
#
# Arka plan:
# Günlük kapanış ait olduğu haftanın
# açılışının altındaysa MAVİ
# =========================================================

def make_daily_flow(
    completed_daily
):

    week_open_map = (
        build_week_open_map(
            completed_daily
        )
    )

    result = []

    for candle in completed_daily[-7:]:

        w_key = week_key(
            candle
        )

        weekly_open = (
            week_open_map.get(
                w_key
            )
        )

        below_parent_open = False

        if weekly_open is not None:

            below_parent_open = (
                candle["close"]
                < weekly_open
            )

        result.append({
            "direction": candle_direction(
                candle
            ),

            "below_parent_open":
                below_parent_open
        })

    return result


# =========================================================
# 4 SAATLİK MUM AKIŞI
#
# Son 6 KAPANMIŞ 4H mum
# =========================================================

def get_symbol_h4_flow(
    symbol
):

    inst_id = to_okx_symbol(
        symbol
    )

    if not inst_id:
        return None

    candles = get_candles(
        inst_id,
        "4H",
        10
    )

    completed = [
        c
        for c in candles
        if c["confirm"] == "1"
    ]

    completed = completed[-6:]

    if len(completed) < 6:
        return None

    return [
        {
            "direction":
                candle_direction(
                    candle
                ),

            "below_parent_open":
                False
        }

        for candle in completed
    ]


# =========================================================
# 1 SAATLİK MUM AKIŞI
#
# Son 4 KAPANMIŞ 1H mum
# =========================================================

def get_symbol_h1_flow(
    symbol
):

    inst_id = to_okx_symbol(
        symbol
    )

    if not inst_id:
        return None

    candles = get_candles(
        inst_id,
        "1H",
        8
    )

    completed = [
        c
        for c in candles
        if c["confirm"] == "1"
    ]

    completed = completed[-4:]

    if len(completed) < 4:
        return None

    return [
        {
            "direction":
                candle_direction(
                    candle
                ),

            "below_parent_open":
                False
        }

        for candle in completed
    ]


# =========================================================
# 4H CACHE
#
# Aynı 4 saatlik blok içinde tekrar çekilmez.
# =========================================================

@lru_cache(maxsize=8)
def get_h4_flow_snapshot(
    coins_tuple,
    four_hour_key
):

    results = {}

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        futures = {
            executor.submit(
                get_symbol_h4_flow,
                symbol
            ): symbol

            for symbol in coins_tuple
        }

        for future in as_completed(
            futures
        ):

            symbol = futures[
                future
            ]

            try:

                value = future.result()

                if value:

                    results[
                        symbol
                    ] = value

            except Exception as e:

                print(
                    f"4H Mum Akışı "
                    f"{symbol}: {e}"
                )

    return results


# =========================================================
# 1H CACHE
#
# Aynı saat içinde tekrar çekilmez.
# =========================================================

@lru_cache(maxsize=8)
def get_h1_flow_snapshot(
    coins_tuple,
    hour_key
):

    results = {}

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        futures = {
            executor.submit(
                get_symbol_h1_flow,
                symbol
            ): symbol

            for symbol in coins_tuple
        }

        for future in as_completed(
            futures
        ):

            symbol = futures[
                future
            ]

            try:

                value = future.result()

                if value:

                    results[
                        symbol
                    ] = value

            except Exception as e:

                print(
                    f"1H Mum Akışı "
                    f"{symbol}: {e}"
                )

    return results


# =========================================================
# ANA MUM AKIŞI MOTORU
#
# Her coin:
#
# 4 Haftalık
# 7 Günlük
# 6 x 4H
# 4 x 1H
#
# TOPLAM = 21 KAPANMIŞ MUM
# =========================================================

def get_mum_akisi_data(
    coins
):

    coins_tuple = tuple(
        coins
    )


    # -----------------------------------------------------
    # Günlük geçmiş veriyi mevcut cache'den kullan
    # -----------------------------------------------------

    history_map = (
        get_history_snapshot(
            coins_tuple,
            market_day_key()
        )
    )


    # -----------------------------------------------------
    # 4H verisi
    # -----------------------------------------------------

    h4_map = (
        get_h4_flow_snapshot(
            coins_tuple,
            market_4h_key()
        )
    )


    # -----------------------------------------------------
    # 1H verisi
    # -----------------------------------------------------

    h1_map = (
        get_h1_flow_snapshot(
            coins_tuple,
            market_hour_key()
        )
    )


    # -----------------------------------------------------
    # Fiyatlar
    # Tek API isteği
    # -----------------------------------------------------

    ticker_map = (
        get_all_tickers()
    )


    results = []


    for symbol in coins:

        history = history_map.get(
            symbol
        )

        if not history:
            continue


        completed_daily = (
            history["daily"]
        )


        # ---------------------------------------------
        # 4 Haftalık
        # ---------------------------------------------

        weekly = make_weekly_flow(
            completed_daily
        )


        # ---------------------------------------------
        # 7 Günlük
        # ---------------------------------------------

        daily = make_daily_flow(
            completed_daily
        )


        # ---------------------------------------------
        # 6 x 4H
        # ---------------------------------------------

        h4 = h4_map.get(
            symbol,
            []
        )


        # ---------------------------------------------
        # 4 x 1H
        # ---------------------------------------------

        h1 = h1_map.get(
            symbol,
            []
        )


        # ---------------------------------------------
        # 21 kutunun tamamı olmalı
        # ---------------------------------------------

        if len(weekly) != 4:
            continue

        if len(daily) != 7:
            continue

        if len(h4) != 6:
            continue

        if len(h1) != 4:
            continue


        inst_id = history[
            "inst_id"
        ]

        price = ticker_map.get(
            inst_id
        )

        if price is None:
            continue


        results.append({

            "coin":
                symbol.replace(
                    "USDT",
                    ""
                ),

            "price":
                f"{price:.8g}",

            "weekly":
                weekly,

            "daily":
                daily,

            "h4":
                h4,

            "h1":
                h1
        })


    return results

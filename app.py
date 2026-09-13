import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from coins import COINS
import binance_data

get_scanner_data = binance_data.get_scanner_data

# Mum Akışı motorunu binance_data.py'ye bir sonraki adımda ekleyeceğiz.
get_mum_akisi_data = getattr(
    binance_data,
    "get_mum_akisi_data",
    None
)


st.set_page_config(
    page_title="Kripto Piyasa Tarayıcısı",
    layout="wide"
)

st.title("Kripto Piyasa Tarayıcısı")
st.caption(
    "OKX USDT Perpetual • Gün / Hafta / Ay / Yıl Konum Paneli"
)


# =========================================================
# ANA VERİ
# =========================================================

@st.cache_data(ttl=60)
def load_data():
    return get_scanner_data(COINS)


start = time.time()

with st.spinner("Coinler taranıyor..."):
    data = load_data()

elapsed = time.time() - start


if not data:
    st.error("Veri alınamadı.")
    st.stop()


df = pd.DataFrame(data)


# =========================================================
# 12 SEVİYE
#
# CLOSE YOK
#
# Gün O/H/L
# Hafta O/H/L
# Ay O/H/L
# Yıl O/H/L
# =========================================================

LEVEL_COLUMNS = [
    "Gün O",
    "Gün H",
    "Gün L",

    "Hafta O",
    "Hafta H",
    "Hafta L",

    "Ay O",
    "Ay H",
    "Ay L",

    "Yıl O",
    "Yıl H",
    "Yıl L"
]


def count_above(row):
    return sum(
        row["Fiyat"] > row[col]
        for col in LEVEL_COLUMNS
    )


def count_below(row):
    return sum(
        row["Fiyat"] < row[col]
        for col in LEVEL_COLUMNS
    )


df["Üstünde"] = df.apply(
    count_above,
    axis=1
)

df["Altında"] = df.apply(
    count_below,
    axis=1
)


# =========================================================
# SIRALAMA
# =========================================================

df = df.sort_values(
    by="Gün %",
    ascending=False
).reset_index(drop=True)


# =========================================================
# PİYASA ÖZETİ
# =========================================================

yukselen = int(
    (df["Gün %"] > 0).sum()
)

dusen = int(
    (df["Gün %"] < 0).sum()
)

acilis_ustu = int(
    (df["Gün Durum"] == "ÜSTÜ").sum()
)

acilis_alti = int(
    (df["Gün Durum"] == "ALTI").sum()
)


c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric(
    "Taranan Coin",
    len(df)
)

c2.metric(
    "Tarama Süresi",
    f"{elapsed:.2f} sn"
)

c3.metric(
    "Günlük Yükselen",
    yukselen
)

c4.metric(
    "Günlük Düşen",
    dusen
)

c5.metric(
    "Gün Açılışı Üstü",
    acilis_ustu
)

c6.metric(
    "Gün Açılışı Altı",
    acilis_alti
)


st.divider()


# =========================================================
# SEKME YAPISI
# =========================================================

tab1, tab2, tab3 = st.tabs([
    "📊 Piyasa Genel Bakış",
    "🎯 12 Seviye Konumu",
    "🟩 Mum Akışı / Trend Yapısı"
])


# =========================================================
# SEKME 1
# PİYASA GENEL BAKIŞ
# =========================================================

with tab1:

    DISPLAY_COLUMNS = [
        "Coin",
        "Fiyat",

        "Gün %",
        "Hafta %",

        "Gün Durum",

        "Üstünde",
        "Altında",

        "Gün Konum %",
        "Hafta Konum %",
        "Ay Konum %",
        "Yıl Konum %",

        "Gün O",
        "Gün H",
        "Gün L",
        "Gün C",

        "Hafta O",
        "Hafta H",
        "Hafta L",
        "Hafta C",

        "Ay O",
        "Ay H",
        "Ay L",
        "Ay C",

        "Yıl O",
        "Yıl H",
        "Yıl L",
        "Yıl C",

        "Gün H Uzaklık %",
        "Gün L Uzaklık %",

        "Son 5 Gün",

        "Gün Hacim USDT",
        "14G Ort Hacim",
        "14G Hacim Fark %"
    ]


    table = df[
        DISPLAY_COLUMNS
    ].copy()


    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=760,

        column_config={

            "Fiyat": st.column_config.NumberColumn(
                "Fiyat",
                format="%.8g"
            ),

            "Gün %": st.column_config.NumberColumn(
                "Gün %",
                format="%.2f%%"
            ),

            "Hafta %": st.column_config.NumberColumn(
                "Hafta %",
                format="%.2f%%"
            ),

            "Gün Konum %": st.column_config.NumberColumn(
                "Gün Konum %",
                format="%.1f%%"
            ),

            "Hafta Konum %": st.column_config.NumberColumn(
                "Hafta Konum %",
                format="%.1f%%"
            ),

            "Ay Konum %": st.column_config.NumberColumn(
                "Ay Konum %",
                format="%.1f%%"
            ),

            "Yıl Konum %": st.column_config.NumberColumn(
                "Yıl Konum %",
                format="%.1f%%"
            ),

            "Gün H Uzaklık %": st.column_config.NumberColumn(
                "Gün High Uzaklık %",
                format="%.2f%%"
            ),

            "Gün L Uzaklık %": st.column_config.NumberColumn(
                "Gün Low Uzaklık %",
                format="%.2f%%"
            ),

            "Gün Hacim USDT": st.column_config.NumberColumn(
                "Gün Hacim",
                format="%.0f"
            ),

            "14G Ort Hacim": st.column_config.NumberColumn(
                "14G Ort Hacim",
                format="%.0f"
            ),

            "14G Hacim Fark %": st.column_config.NumberColumn(
                "14G Hacim Fark %",
                format="%.1f%%"
            )
        }
    )


    st.caption(
        "Sütun başlıklarına dokunarak yüksekten düşüğe "
        "veya düşükten yükseğe sıralayabilirsin."
    )


# =========================================================
# SEKME 2
# 12 SEVİYE KONUMU
# =========================================================

with tab2:

    st.subheader("12 Seviye Konumu")

    st.caption(
        "Günlük + Haftalık + Aylık + Yıllık "
        "Açılış / En Yüksek / En Düşük seviyeleri"
    )


    def fmt_price(value):
        try:
            return f"{float(value):.8g}"
        except:
            return str(value)


    def level_percent(price, level):

        if level == 0:
            return 0.0

        return (
            (price - level)
            / level
            * 100
        )


    def level_cell(price, level):

        pct = level_percent(
            price,
            level
        )

        if pct > 0:
            color = "#16c784"
            sign = "+"

        elif pct < 0:
            color = "#ea3943"
            sign = ""

        else:
            color = "#8b949e"
            sign = ""

        return f"""
        <div class="level-cell">
            <div class="level-price">
                {fmt_price(level)}
            </div>

            <div
                class="level-pct"
                style="color:{color};"
            >
                {sign}{pct:.2f}%
            </div>
        </div>
        """


    html = """
    <!DOCTYPE html>
    <html>

    <head>

    <meta charset="utf-8">

    <style>

        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: transparent;
        }

        .ohlc-wrap {
            width: 100%;
            overflow-x: auto;
            overflow-y: auto;
        }

        .ohlc-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            font-size: 11px;
        }

        .ohlc-table th {
            background: #f4f6f8;
            border: 1px solid #dfe3e8;
            padding: 5px 2px;
            text-align: center;
            font-weight: 700;
            white-space: nowrap;
        }

        .ohlc-table td {
            border: 1px solid #e5e7eb;
            padding: 3px 2px;
            text-align: center;
            vertical-align: middle;
        }

        .coin-cell {
            font-weight: 700;
            white-space: nowrap;
            width: 58px;
        }

        .current-price {
            font-weight: 700;
            white-space: nowrap;
            width: 62px;
        }

        .level-cell {
            line-height: 1.0;
            min-width: 46px;
        }

        .level-price {
            font-size: 10px;
            font-weight: 600;
            white-space: nowrap;
        }

        .level-pct {
            margin-top: 2px;
            font-size: 9px;
            font-weight: 700;
            white-space: nowrap;
        }

        .count-up {
            font-size: 13px;
            font-weight: 800;
            color: #16c784;
        }

        .count-down {
            font-size: 13px;
            font-weight: 800;
            color: #ea3943;
        }

    </style>

    </head>

    <body>

    <div class="ohlc-wrap">

    <table class="ohlc-table">

    <thead>

        <tr>

            <th rowspan="2">
                Coin
            </th>

            <th rowspan="2">
                Fiyat
            </th>

            <th colspan="3">
                Günlük
            </th>

            <th colspan="3">
                Haftalık
            </th>

            <th colspan="3">
                Aylık
            </th>

            <th colspan="3">
                Yıllık
            </th>

            <th rowspan="2">
                Üstü
            </th>

            <th rowspan="2">
                Altı
            </th>

        </tr>

        <tr>

            <th>O</th>
            <th>H</th>
            <th>L</th>

            <th>O</th>
            <th>H</th>
            <th>L</th>

            <th>O</th>
            <th>H</th>
            <th>L</th>

            <th>O</th>
            <th>H</th>
            <th>L</th>

        </tr>

    </thead>

    <tbody>
    """


    for _, row in df.iterrows():

        price = float(
            row["Fiyat"]
        )

        html += f"""
        <tr>

            <td class="coin-cell">
                {row["Coin"]}
            </td>

            <td class="current-price">
                {fmt_price(price)}
            </td>

            <td>{level_cell(price, row["Gün O"])}</td>
            <td>{level_cell(price, row["Gün H"])}</td>
            <td>{level_cell(price, row["Gün L"])}</td>

            <td>{level_cell(price, row["Hafta O"])}</td>
            <td>{level_cell(price, row["Hafta H"])}</td>
            <td>{level_cell(price, row["Hafta L"])}</td>

            <td>{level_cell(price, row["Ay O"])}</td>
            <td>{level_cell(price, row["Ay H"])}</td>
            <td>{level_cell(price, row["Ay L"])}</td>

            <td>{level_cell(price, row["Yıl O"])}</td>
            <td>{level_cell(price, row["Yıl H"])}</td>
            <td>{level_cell(price, row["Yıl L"])}</td>

            <td class="count-up">
                {int(row["Üstünde"])}/12
            </td>

            <td class="count-down">
                {int(row["Altında"])}/12
            </td>

        </tr>
        """


    html += """
    </tbody>

    </table>

    </div>

    </body>

    </html>
    """


    components.html(
        html,
        height=760,
        scrolling=True
    )


    st.caption(
        "Yeşil yüzde: fiyat seviyenin üzerinde • "
        "Kırmızı yüzde: fiyat seviyenin altında"
    )


# =========================================================
# SEKME 3
# MUM AKIŞI / TREND YAPISI
# =========================================================

with tab3:

    st.subheader(
        "Mum Akışı / Trend Yapısı"
    )

    st.caption(
        "Her coin için 21 kapanmış mum: "
        "4 Haftalık + 7 Günlük + 6×4H + 4×1H"
    )


    # -----------------------------------------------------
    # BINANCE_DATA MOTORU HENÜZ EKLENMEDİYSE
    # -----------------------------------------------------

    if get_mum_akisi_data is None:

        st.info(
            "Mum Akışı veri motoru henüz eklenmedi. "
            "Bir sonraki adımda binance_data.py güncellenecek."
        )

    else:

        @st.cache_data(ttl=60)
        def load_mum_akisi():
            return get_mum_akisi_data(
                COINS
            )


        with st.spinner(
            "Mum akışı verileri hazırlanıyor..."
        ):
            flow_data = load_mum_akisi()


        if not flow_data:

            st.warning(
                "Mum Akışı verisi alınamadı."
            )

        else:

            # =================================================
            # KUTU ÜRETİMİ
            # =================================================

            def candle_box(
                candle,
                parent_type=None
            ):

                direction = candle.get(
                    "direction",
                    "doji"
                )

                below_parent = candle.get(
                    "below_parent_open",
                    False
                )


                # ---------------------------------------------
                # MUM RENGİ
                # ---------------------------------------------

                if direction == "up":

                    candle_color = "#00c46a"

                elif direction == "down":

                    candle_color = "#e53935"

                else:

                    candle_color = "#8b949e"


                # ---------------------------------------------
                # ARKA PLAN
                # ---------------------------------------------

                background = "#131b24"
                border = "#263442"


                # Haftalık mum
                # aylık açılış altında
                if (
                    parent_type == "weekly"
                    and below_parent
                ):

                    background = "#31135c"
                    border = "#8e44ff"


                # Günlük mum
                # haftalık açılış altında
                elif (
                    parent_type == "daily"
                    and below_parent
                ):

                    background = "#082f55"
                    border = "#168cff"


                return f"""
                <div
                    class="candle-box"
                    style="
                        background:{background};
                        border-color:{border};
                    "
                >
                    <div
                        class="candle-inner"
                        style="
                            background:{candle_color};
                        "
                    ></div>
                </div>
                """


            # =================================================
            # HTML
            # =================================================

            flow_html = """
            <!DOCTYPE html>

            <html>

            <head>

            <meta charset="utf-8">

            <style>

                body {
                    margin:0;
                    padding:0;
                    font-family:Arial, sans-serif;
                    background:transparent;
                }

                .flow-wrap {
                    width:100%;
                    overflow-x:auto;
                    overflow-y:auto;
                }

                .flow-table {
                    width:100%;
                    border-collapse:collapse;
                    font-size:11px;
                }

                .flow-table th {
                    background:#f4f6f8;
                    border:1px solid #dfe3e8;
                    padding:6px 4px;
                    text-align:center;
                    white-space:nowrap;
                }

                .flow-table td {
                    border:1px solid #e5e7eb;
                    padding:5px 3px;
                    text-align:center;
                    vertical-align:middle;
                }

                .coin-name {
                    min-width:70px;
                    font-weight:800;
                }

                .price-cell {
                    min-width:70px;
                    font-weight:700;
                }

                .boxes {
                    display:flex;
                    justify-content:center;
                    gap:4px;
                    white-space:nowrap;
                }

                .candle-box {
                    width:30px;
                    height:30px;

                    display:flex;
                    align-items:center;
                    justify-content:center;

                    border:2px solid #263442;
                    border-radius:5px;

                    box-sizing:border-box;
                }

                .candle-inner {
                    width:18px;
                    height:18px;

                    border-radius:3px;
                }

                .weekly-group {
                    min-width:145px;
                }

                .daily-group {
                    min-width:245px;
                }

                .h4-group {
                    min-width:215px;
                }

                .h1-group {
                    min-width:145px;
                }

                .legend {
                    margin-bottom:12px;
                    font-size:11px;
                    line-height:1.6;
                }

                .green {
                    color:#00a85a;
                    font-weight:700;
                }

                .red {
                    color:#d9363e;
                    font-weight:700;
                }

                .gray {
                    color:#7a828a;
                    font-weight:700;
                }

                .purple {
                    color:#9147ff;
                    font-weight:700;
                }

                .blue {
                    color:#168cff;
                    font-weight:700;
                }

            </style>

            </head>


            <body>


            <div class="legend">

                <span class="green">
                    ■ Yeşil = Yükseliş
                </span>

                &nbsp;&nbsp;

                <span class="red">
                    ■ Kırmızı = Düşüş
                </span>

                &nbsp;&nbsp;

                <span class="gray">
                    ■ Gri = Doji
                </span>

                <br>

                <span class="purple">
                    ■ Mor arka plan =
                    Haftalık mum aylık açılışın altında
                </span>

                &nbsp;&nbsp;

                <span class="blue">
                    ■ Mavi arka plan =
                    Günlük mum haftalık açılışın altında
                </span>

            </div>


            <div class="flow-wrap">

            <table class="flow-table">

            <thead>

                <tr>

                    <th>
                        Coin
                    </th>

                    <th>
                        Haftalık (4)
                        <br>
                        <small>
                            Aylık Açılışa Göre
                        </small>
                    </th>

                    <th>
                        Günlük (7)
                        <br>
                        <small>
                            Haftalık Açılışa Göre
                        </small>
                    </th>

                    <th>
                        4 Saatlik (6)
                    </th>

                    <th>
                        1 Saatlik (4)
                    </th>

                    <th>
                        Fiyat
                    </th>

                </tr>

            </thead>

            <tbody>
            """


            for coin in flow_data:

                weekly = coin.get(
                    "weekly",
                    []
                )

                daily = coin.get(
                    "daily",
                    []
                )

                h4 = coin.get(
                    "h4",
                    []
                )

                h1 = coin.get(
                    "h1",
                    []
                )

                current_price = coin.get(
                    "price",
                    ""
                )


                weekly_boxes = "".join(
                    candle_box(
                        candle,
                        "weekly"
                    )
                    for candle in weekly
                )


                daily_boxes = "".join(
                    candle_box(
                        candle,
                        "daily"
                    )
                    for candle in daily
                )


                h4_boxes = "".join(
                    candle_box(
                        candle
                    )
                    for candle in h4
                )


                h1_boxes = "".join(
                    candle_box(
                        candle
                    )
                    for candle in h1
                )


                flow_html += f"""
                <tr>

                    <td class="coin-name">
                        {coin.get("coin", "")}
                    </td>

                    <td class="weekly-group">
                        <div class="boxes">
                            {weekly_boxes}
                        </div>
                    </td>

                    <td class="daily-group">
                        <div class="boxes">
                            {daily_boxes}
                        </div>
                    </td>

                    <td class="h4-group">
                        <div class="boxes">
                            {h4_boxes}
                        </div>
                    </td>

                    <td class="h1-group">
                        <div class="boxes">
                            {h1_boxes}
                        </div>
                    </td>

                    <td class="price-cell">
                        {current_price}
                    </td>

                </tr>
                """


            flow_html += """
            </tbody>

            </table>

            </div>

            </body>

            </html>
            """


            components.html(
                flow_html,
                height=820,
                scrolling=True
            )

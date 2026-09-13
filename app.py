import time
import streamlit as st
import pandas as pd

from coins import COINS
from binance_data import get_scanner_data


st.set_page_config(
    page_title="Kripto Piyasa Tarayıcısı",
    layout="wide"
)

st.title("Kripto Piyasa Tarayıcısı")
st.caption("OKX USDT Perpetual • Gün / Hafta / Ay / Yıl Konum Paneli")


# =========================================================
# VERİ
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
#
# Toplam = 12
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
# İLK AÇILIŞTA EN ÇOK YÜKSELENLER ÜSTTE
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

tab1, tab2 = st.tabs([
    "📊 Piyasa Genel Bakış",
    "🎯 12 Seviye Konumu"
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


    # -----------------------------------------------------
    # FİYAT FORMAT
    # -----------------------------------------------------

    def fmt_price(value):
        try:
            return f"{float(value):.8g}"
        except:
            return str(value)


    # -----------------------------------------------------
    # SEVİYEYE GÖRE YÜZDE
    #
    # + = fiyat seviyenin üzerinde
    # - = fiyat seviyenin altında
    # -----------------------------------------------------

    def level_percent(price, level):

        if level == 0:
            return 0.0

        return (
            (price - level)
            / level
            * 100
        )


    # -----------------------------------------------------
    # TEK HÜCRE
    #
    # Fiyat üstte
    # Yüzde altta
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # CSS
    #
    # Amaç:
    # 12 seviyeyi mümkün olduğunca tek ekrana sığdırmak
    # -----------------------------------------------------

    st.markdown(
        """
        <style>

        .ohlc-wrap {
            width: 100%;
            overflow-x: auto;
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
            width: 55px;
        }

        .current-price {
            font-weight: 700;
            white-space: nowrap;
            width: 60px;
        }

        .level-cell {
            line-height: 1.05;
            min-width: 50px;
        }

        .level-price {
            font-size: 10px;
            font-weight: 600;
            white-space: nowrap;
        }

        .level-pct {
            margin-top: 3px;
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

        .period-head {
            font-size: 11px;
            font-weight: 800;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # TABLO HTML
    # -----------------------------------------------------

    html = """
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

            <td>
                {level_cell(price, row["Gün O"])}
            </td>

            <td>
                {level_cell(price, row["Gün H"])}
            </td>

            <td>
                {level_cell(price, row["Gün L"])}
            </td>

            <td>
                {level_cell(price, row["Hafta O"])}
            </td>

            <td>
                {level_cell(price, row["Hafta H"])}
            </td>

            <td>
                {level_cell(price, row["Hafta L"])}
            </td>

            <td>
                {level_cell(price, row["Ay O"])}
            </td>

            <td>
                {level_cell(price, row["Ay H"])}
            </td>

            <td>
                {level_cell(price, row["Ay L"])}
            </td>

            <td>
                {level_cell(price, row["Yıl O"])}
            </td>

            <td>
                {level_cell(price, row["Yıl H"])}
            </td>

            <td>
                {level_cell(price, row["Yıl L"])}
            </td>

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
    """


    st.markdown(
        html,
        unsafe_allow_html=True
    )


    st.caption(
        "Yeşil yüzde: fiyat seviyenin üzerinde • "
        "Kırmızı yüzde: fiyat seviyenin altında"
    )

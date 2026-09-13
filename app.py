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
# Gün O/H/L        = 3
# Hafta O/H/L      = 3
# Ay O/H/L         = 3
# Yıl O/H/L        = 3
#
# TOPLAM = 12
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
    # Eşitlik durumunda seviyenin üst tarafında kabul ediyoruz.
    # Böylece Üstünde + Altında her zaman 12 olur.
    return sum(
        row["Fiyat"] >= row[col]
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

df["12 Seviye"] = (
    df["Üstünde"].astype(str)
    + "/12"
)


# =========================================================
# İLK AÇILIŞTA GÜNLÜK EN ÇOK YÜKSELEN ÜSTTE
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
# İKİ ANA PANEL
# =========================================================

tab1, tab2 = st.tabs([
    "📊 Piyasa Genel Bakış",
    "🎯 12 Seviye Konumu"
])


# =========================================================
# TAB 1
# PİYASA GENEL BAKIŞ
# =========================================================

with tab1:

    DISPLAY_COLUMNS = [
        "Coin",
        "Fiyat",

        "Gün %",
        "Hafta %",

        "Gün Durum",

        "12 Seviye",
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
# TAB 2
# 12 SEVİYE KONUMU
# =========================================================

with tab2:

    st.subheader("12 Seviye Konumu")

    st.caption(
        "Günlük + Haftalık + Aylık + Yıllık "
        "Açılış / En Yüksek / En Düşük seviyeleri"
    )


    # -----------------------------------------------------
    # FİYATIN SEVİYEYE YÜZDE KONUMU
    #
    # Pozitif = fiyat seviyenin üzerinde
    # Negatif = fiyat seviyenin altında
    # -----------------------------------------------------

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

        sign = "+" if pct >= 0 else ""

        return (
            f"{level:.8g} "
            f"({sign}{pct:.2f}%)"
        )


    level_table = pd.DataFrame()


    level_table["Coin"] = df["Coin"]

    level_table["Fiyat"] = df["Fiyat"]


    # ---------- GÜNLÜK ----------

    level_table["Gün O"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Gün O"]
        ),
        axis=1
    )

    level_table["Gün H"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Gün H"]
        ),
        axis=1
    )

    level_table["Gün L"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Gün L"]
        ),
        axis=1
    )


    # ---------- HAFTALIK ----------

    level_table["Hafta O"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Hafta O"]
        ),
        axis=1
    )

    level_table["Hafta H"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Hafta H"]
        ),
        axis=1
    )

    level_table["Hafta L"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Hafta L"]
        ),
        axis=1
    )


    # ---------- AYLIK ----------

    level_table["Ay O"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Ay O"]
        ),
        axis=1
    )

    level_table["Ay H"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Ay H"]
        ),
        axis=1
    )

    level_table["Ay L"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Ay L"]
        ),
        axis=1
    )


    # ---------- YILLIK ----------

    level_table["Yıl O"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Yıl O"]
        ),
        axis=1
    )

    level_table["Yıl H"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Yıl H"]
        ),
        axis=1
    )

    level_table["Yıl L"] = df.apply(
        lambda r: level_cell(
            r["Fiyat"],
            r["Yıl L"]
        ),
        axis=1
    )


    level_table["Üstünde"] = df["Üstünde"]

    level_table["Altında"] = df["Altında"]

    level_table["Konum"] = df["12 Seviye"]


    st.dataframe(
        level_table,
        use_container_width=True,
        hide_index=True,
        height=760,

        column_config={

            "Fiyat": st.column_config.NumberColumn(
                "Fiyat",
                format="%.8g"
            ),

            "Üstünde": st.column_config.NumberColumn(
                "Üstünde",
                format="%d"
            ),

            "Altında": st.column_config.NumberColumn(
                "Altında",
                format="%d"
            )
        }
    )


    st.caption(
        "Pozitif yüzde: fiyat seviyenin üzerinde. "
        "Negatif yüzde: fiyat seviyenin altında. "
        "Close değerleri 12 seviye hesabına dahil değildir."
    )

import streamlit as st
import pandas as pd

from coins import COINS
from binance_data import get_scanner_data


st.set_page_config(
    page_title="Kripto Piyasa Tarayıcısı",
    layout="wide"
)

st.title("Kripto Piyasa Tarayıcısı")
st.caption("OKX USDT Perpetual • Piyasa Konum Tarayıcısı")


# Veriyi her ekran hareketinde tekrar çekmemek için 60 saniye önbellek
@st.cache_data(ttl=60)
def load_data():
    return get_scanner_data(COINS)


with st.spinner("Piyasa verileri yükleniyor..."):
    data = load_data()


if not data:
    st.error("OKX verisi alınamadı veya listedeki coinler OKX'te bulunamadı.")
    st.stop()


df = pd.DataFrame(data)


# ---------------------------------------------------------
# 16 OHLC seviyesine göre fiyat kaçının üstünde / altında?
# Gün + Hafta + Ay + Yıl = 4 x OHLC = 16 seviye
# ---------------------------------------------------------

level_columns = [
    "Gün O", "Gün H", "Gün L", "Gün C",
    "Hafta O", "Hafta H", "Hafta L", "Hafta C",
    "Ay O", "Ay H", "Ay L", "Ay C",
    "Yıl O", "Yıl H", "Yıl L", "Yıl C"
]


def count_above(row):
    return sum(
        row["Fiyat"] > row[col]
        for col in level_columns
    )


def count_below(row):
    return sum(
        row["Fiyat"] < row[col]
        for col in level_columns
    )


df["Üstünde"] = df.apply(count_above, axis=1)
df["Altında"] = df.apply(count_below, axis=1)


# ---------------------------------------------------------
# İlk açılışta en çok günlük yükselen üstte
# ---------------------------------------------------------

df = df.sort_values(
    by="Gün %",
    ascending=False
).reset_index(drop=True)


# ---------------------------------------------------------
# Piyasa özeti
# ---------------------------------------------------------

yukselen = int((df["Gün %"] > 0).sum())
dusen = int((df["Gün %"] < 0).sum())

acilis_ustu = int(
    (df["Gün Durum"] == "ÜSTÜ").sum()
)

acilis_alti = int(
    (df["Gün Durum"] == "ALTI").sum()
)


c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Taranan Coin",
    len(df)
)

c2.metric(
    "Günlük Yükselen",
    yukselen
)

c3.metric(
    "Günlük Düşen",
    dusen
)

c4.metric(
    "Gün Açılışı Üstü",
    acilis_ustu
)

c5.metric(
    "Gün Açılışı Altı",
    acilis_alti
)


st.divider()


# ---------------------------------------------------------
# Ana yatay tablo
# ---------------------------------------------------------

display_columns = [
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

    "Gün H Uzaklık %",
    "Gün L Uzaklık %",

    "Son 5 Gün",

    "Gün Hacim USDT",
    "14G Ort Hacim",
    "14G Hacim Fark %"
]


table = df[display_columns].copy()


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=720,

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
            "High Uzaklık %",
            format="%.2f%%"
        ),

        "Gün L Uzaklık %": st.column_config.NumberColumn(
            "Low Uzaklık %",
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
        ),
    }
)


st.caption(
    "Tablodaki herhangi bir sütun başlığına dokunarak "
    "yüksekten düşüğe veya düşükten yükseğe sıralayabilirsin."
)

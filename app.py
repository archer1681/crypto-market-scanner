import streamlit as st
import pandas as pd

from coins import COINS
from binance_data import get_all_prices


st.set_page_config(
    page_title="Kripto Piyasa Tarayıcısı",
    layout="wide"
)

st.title("Kripto Piyasa Tarayıcısı")

data = get_all_prices(COINS)

df = pd.DataFrame(data)

if not df.empty:
    df = df.sort_values(
        by="change_24h",
        ascending=False
    )

    df = df.rename(columns={
        "symbol": "Coin",
        "price": "Fiyat",
        "change_24h": "24s %",
        "volume": "Günlük Hacim"
    })

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Binance verisi alınamadı.")

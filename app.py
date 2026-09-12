import time
import streamlit as st
import pandas as pd

from binance_data import get_scanner_data


st.set_page_config(
    page_title="Kripto Tarayıcı Test",
    layout="wide"
)

st.title("Kripto Tarayıcı - 5 Coin Test")


TEST_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "AAVEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "BNBUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "OPUSDT",
    "ARBUSDT",
    "SUIUSDT",
    "INJUSDT",
    "TRXUSDT",
    "UNIUSDT"
]


@st.cache_data(ttl=60)
def load_test_data():
    return get_scanner_data(TEST_COINS)


start = time.time()

with st.spinner("5 coin taranıyor..."):
    data = load_test_data()

elapsed = time.time() - start


st.write(
    "Tarama süresi:",
    round(elapsed, 2),
    "saniye"
)


if not data:
    st.error("Hiç veri alınamadı.")
    st.stop()


df = pd.DataFrame(data)


columns = [
    "Coin",
    "Fiyat",
    "Gün %",
    "Hafta %",
    "Gün Durum",
    "Gün Konum %",
    "Hafta Konum %",
    "Ay Konum %",
    "Yıl Konum %",
    "Son 5 Gün",
    "Gün Hacim USDT",
    "14G Hacim Fark %"
]


st.success(
    f"{len(df)} coin başarıyla tarandı."
)


st.dataframe(
    df[columns],
    use_container_width=True,
    hide_index=True
)

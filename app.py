import streamlit as st
import requests
import time

st.set_page_config(
    page_title="OKX Mum Veri Testi",
    layout="wide"
)

st.title("OKX Mum Veri Testi")

# 1) SWAP listesini test et
st.subheader("1. OKX sözleşme listesi")

try:
    start = time.time()

    r1 = requests.get(
        "https://www.okx.com/api/v5/public/instruments",
        params={"instType": "SWAP"},
        timeout=10
    )

    elapsed1 = time.time() - start

    st.write("HTTP:", r1.status_code)
    st.write("Süre:", round(elapsed1, 2), "saniye")

    j1 = r1.json()
    st.write("OKX kodu:", j1.get("code"))

except Exception as e:
    st.error("Sözleşme listesi hatası")
    st.code(str(e))


# 2) Gerçek kullandığımız günlük mum endpoint'i
st.subheader("2. BTC günlük mum verisi")

try:
    start = time.time()

    r2 = requests.get(
        "https://www.okx.com/api/v5/market/candles",
        params={
            "instId": "BTC-USDT-SWAP",
            "bar": "1Dutc",
            "limit": "5"
        },
        timeout=10
    )

    elapsed2 = time.time() - start

    st.write("HTTP:", r2.status_code)
    st.write("Süre:", round(elapsed2, 2), "saniye")

    j2 = r2.json()

    st.write("OKX kodu:", j2.get("code"))
    st.write("Mum sayısı:", len(j2.get("data", [])))

    if j2.get("code") == "0" and j2.get("data"):
        st.success("GÜNLÜK MUM VERİSİ BAŞARILI")
        st.write("Son mum:")
        st.code(str(j2["data"][0]))
    else:
        st.error("Mum verisi alınamadı")
        st.code(r2.text)

except Exception as e:
    st.error("Mum bağlantı hatası")
    st.code(str(e))

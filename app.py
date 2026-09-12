import streamlit as st
import requests

st.set_page_config(
    page_title="Binance Bağlantı Testi",
    layout="wide"
)

st.title("Binance Bağlantı Testi")

url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
params = {"symbol": "BTCUSDT"}

try:
    response = requests.get(
        url,
        params=params,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    st.write("HTTP durum kodu:", response.status_code)
    st.write("Binance cevabı:")
    st.code(response.text)

except Exception as e:
    st.error("Bağlantı hatası:")
    st.code(str(e))

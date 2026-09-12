import streamlit as st
import requests

st.set_page_config(
    page_title="OKX Bağlantı Testi",
    layout="wide"
)

st.title("OKX Bağlantı Testi")

url = "https://www.okx.com/api/v5/market/ticker"
params = {"instId": "BTC-USDT-SWAP"}

try:
    response = requests.get(
        url,
        params=params,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    st.write("HTTP durum kodu:", response.status_code)
    st.write("OKX cevabı:")

    st.code(response.text)

    if response.status_code == 200:
        data = response.json()

        if data.get("code") == "0" and data.get("data"):
            fiyat = data["data"][0]["last"]
            st.success("OKX BAĞLANTISI BAŞARILI")
            st.write("BTC-USDT-SWAP fiyatı:", fiyat)
        else:
            st.error("OKX cevap verdi ancak veri alınamadı.")
    else:
        st.error("OKX bağlantısı başarısız.")

except Exception as e:
    st.error("Bağlantı hatası:")
    st.code(str(e))

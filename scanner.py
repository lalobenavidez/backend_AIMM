import streamlit as st
import yfinance as yf
import pandas as pd

# Lista de tickers
tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "NVDA"]

st.title("📈 Dashboard Financiero Simple")
st.subheader("Selecciona un ticker para ver sus datos:")

# Dropdown
selected_ticker = st.selectbox("Ticker", tickers)

# Descargar datos de 1h para los últimos 5 días
df = yf.download(selected_ticker, period="5d", interval="60m", progress=False)
df.dropna(inplace=True)

# Calcular EMAs
df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

# Último dato disponible
ultima = df.iloc[-1]
precio = round(ultima["Close"], 2)
ema20 = round(ultima["EMA20"], 2)
ema50 = round(ultima["EMA50"], 2)

# Calcular pivots clásicos usando el penúltimo día completo
df["Date"] = df.index.date
ultimo_dia_completo = df["Date"].unique()[-2]
df_dia = df[df["Date"] == ultimo_dia_completo]
high = df_dia["High"].max()
low = df_dia["Low"].min()
close_prev = df_dia["Close"].iloc[-1]

pp = round((high + low + close_prev) / 3, 2)
r1 = round((2 * pp) - low, 2)
r2 = round(pp + (high - low), 2)
s1 = round((2 * pp) - high, 2)
s2 = round(pp - (high - low), 2)

# Mostrar resultados
st.markdown(f"### 📊 Datos para {selected_ticker}")
st.write(f"**Precio actual:** ${precio}")
st.write(f"**EMA20:** ${ema20}")
st.write(f"**EMA50:** ${ema50}")

st.markdown("### 🔹 Pivots clásicos (basados en el día anterior):")
st.write(f"**PP:** {pp}")
st.write(f"**R1:** {r1}")
st.write(f"**R2:** {r2}")
st.write(f"**S1:** {s1}")
st.write(f"**S2:** {s2}")
